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
  if id:match("^fig:[a-z0-9][a-z0-9_-]*$") then
    return {
      pandoc.RawInline("latex", "\\figurename~\\ref{" .. id .. "}")
    }
  end

  if id:match("^tbl:[a-z0-9][a-z0-9_-]*$") then
    return {
      pandoc.RawInline("latex", "\\tablename~\\ref{" .. id .. "}")
    }
  end

  return nil
end

function Pandoc(document)
  return document:walk({
    Cite = resolve_cite,
  })
end
