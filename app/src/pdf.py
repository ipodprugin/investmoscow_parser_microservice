import pdfplumber


async def search_fields_in_table(rows, search_fields):
    fields = {}
    search_fields = search_fields.copy()
    for row in reversed(rows):
        for field in search_fields:
            if field in row:
                fields[field] = row[-2]
                search_fields.remove(field)
                break
    return fields, search_fields


async def _search_fields_on_page(page, search_fields):
    tables = page.extract_tables()
    for table in tables:
        found_fields, not_found_fields = await search_fields_in_table(table, search_fields)
        if found_fields:
            return found_fields, not_found_fields
    return None, search_fields


async def search_fields_on_page(page, search_fields):
    ...


async def search_fields_in_pdf(pdf_path, search_fields):
    # TODO: найти как из содержания документа переходить сразу по ссылке в заголовке:
    # Точное описание объекта оценки с приведением ссылок на документы, устанавливающие качественные и количественные характеристики объекта оценки
    found_fields = {}

    with pdfplumber.open(pdf_path) as pdf:
        # для ускорения начинаем поиск с этих страниц, так как чаще всего данные находятся в этом диапазоне
        pages = pdf.pages[12:20]

        for page in pages:
            _found_fields, not_found_fields = await _search_fields_on_page(page, search_fields)
            if _found_fields:
                found_fields.update(_found_fields)
            if not not_found_fields:
                return found_fields
            else:
                search_fields = not_found_fields

        # TODO: сделать поиск реверсивно от 12 стр к началу и от 20 к концу
        for index, page in enumerate(pdf.pages):
            if index >= 12 and index < 20:
                continue

            _found_fields, not_found_fields = await _search_fields_on_page(page, search_fields)
            if _found_fields:
                found_fields.update(_found_fields)
            if not not_found_fields:
                return found_fields
            else:
                search_fields = not_found_fields

    return found_fields

