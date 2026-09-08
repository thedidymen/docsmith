-- Apply author-supplied relative weights to Pandoc's native table colspecs.

local attribute_name = "column-widths"

-- Pandoc's table_captions extension treats a trailing attribute block as caption
-- text (unlike image attributes). Promote the documented caption form into the
-- Table Attr in the AST, without rewriting Markdown source.
local function promote_caption_attributes(table)
  if table.caption == nil or table.caption.long == nil or #table.caption.long == 0 then
    return false
  end

  local block = table.caption.long[#table.caption.long]
  if block.content == nil then
    return false
  end

  local attribute_start = nil
  for index, inline in ipairs(block.content) do
    if inline.tag == "Str" and inline.text:match("^%{") then
      attribute_start = index
      break
    end
  end
  if attribute_start == nil then
    return false
  end

  local suffix = {}
  for index = attribute_start, #block.content do
    suffix[#suffix + 1] = block.content[index]
  end
  local source = pandoc.utils.stringify(suffix)
  if not source:match("^%{.*%}$") then
    return false
  end

  local identifier = source:match("#([%w][%w:_-]*)")
  local widths = source:match('column%-widths%s*=%s*"([^"]*)"')
    or source:match("column%-widths%s*=%s*“([^”]*)”")
  if identifier == nil and widths == nil then
    return false
  end

  if identifier ~= nil then
    table.identifier = identifier
  end
  if widths ~= nil then
    table.attributes[attribute_name] = widths
  end

  for index = #block.content, attribute_start, -1 do
    block.content:remove(index)
  end
  if #block.content > 0 and block.content[#block.content].tag == "Space" then
    block.content:remove(#block.content)
  end
  return true
end

local function table_name(table)
  if table.identifier ~= nil and table.identifier ~= "" then
    return "Table `" .. table.identifier .. "`"
  end
  return "Table"
end

local function fail(table, message)
  error(table_name(table) .. ": invalid `" .. attribute_name .. "`: " .. message, 0)
end

local function parse_weights(table, raw, column_count)
  local weights = {}

  -- Appending a comma makes empty leading, trailing, and adjacent fields visible.
  for value in (raw .. ","):gmatch("(.-),") do
    local trimmed = value:match("^%s*(.-)%s*$")
    local weight = tonumber(trimmed)
    local position = #weights + 1

    if trimmed == "" or weight == nil or weight ~= weight or weight == math.huge or weight == -math.huge then
      fail(table, "value " .. position .. " (`" .. trimmed .. "`) is not a finite number")
    end
    if weight <= 0 then
      fail(table, "value " .. position .. " must be greater than zero; received `" .. trimmed .. "`")
    end
    weights[position] = weight
  end

  if #weights ~= column_count then
    fail(
      table,
      "expected " .. column_count .. " values for " .. column_count
        .. " columns, but received " .. #weights
    )
  end

  return weights
end

function Table(table)
  local attributes_promoted = promote_caption_attributes(table)
  local raw = table.attributes[attribute_name]
  if raw == nil then
    return attributes_promoted and table or nil
  end

  local weights = parse_weights(table, raw, #table.colspecs)
  local total = 0
  for _, weight in ipairs(weights) do
    total = total + weight
  end

  for index, colspec in ipairs(table.colspecs) do
    table.colspecs[index] = { colspec[1], weights[index] / total }
  end

  -- This is a Docsmith authoring attribute, not writer-facing presentation data.
  table.attributes[attribute_name] = nil
  return table
end
