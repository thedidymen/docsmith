local figure_numbers = {}
local table_numbers = {}
local figure_counter = 0
local table_counter = 0

local function identifier_of(element)
  if element.identifier ~= nil then
    return element.identifier
  end
  if element.attr ~= nil and element.attr.identifier ~= nil then
    return element.attr.identifier
  end
  return ""
end

local function register_figure(identifier)
  if identifier:match("^fig:[a-z0-9][a-z0-9_-]*$") and figure_numbers[identifier] == nil then
    figure_counter = figure_counter + 1
    figure_numbers[identifier] = figure_counter
  end
end

local function register_table(identifier)
  if identifier:match("^tbl:[a-z0-9][a-z0-9_-]*$") and table_numbers[identifier] == nil then
    table_counter = table_counter + 1
    table_numbers[identifier] = table_counter
  end
end

local function collect_block(block)
  if block.t == "Figure" then
    register_figure(identifier_of(block))
    return nil
  end

  if block.t == "Table" then
    register_table(identifier_of(block))
    return nil
  end

  if (block.t == "Para" or block.t == "Plain") and #block.content == 1 then
    local only = block.content[1]
    if only.t == "Image" then
      register_figure(identifier_of(only))
    end
  end

  return nil
end

local function resolve_cite(element)
  if #element.citations ~= 1 then
    return nil
  end

  local citation = element.citations[1]
  if citation.prefix ~= nil and #citation.prefix > 0 then
    return nil
  end
  if citation.suffix ~= nil and #citation.suffix > 0 then
    return nil
  end

  local id = citation.id
  local figure_number = figure_numbers[id]
  if figure_number ~= nil then
    return { pandoc.Str("Figure " .. tostring(figure_number)) }
  end

  local table_number = table_numbers[id]
  if table_number ~= nil then
    return { pandoc.Str("Table " .. tostring(table_number)) }
  end

  return nil
end

function Pandoc(document)
  document = document:walk({
    Figure = collect_block,
    Table = collect_block,
    Para = collect_block,
    Plain = collect_block,
  })

  return document:walk({
    Cite = resolve_cite,
  })
end
