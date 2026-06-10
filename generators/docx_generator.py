# -*- coding: utf-8 -*-
"""
Генерация коммерческого предложения в формате DOCX.
Чистая реализация без дублирования с PDF.
"""
import os
import re
from datetime import datetime
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import config


# ==================== ЦВЕТОВЫЕ КОНСТАНТЫ ====================
COLOR_SUBTITLE = RGBColor(0x71, 0x80, 0x96)
COLOR_ADDRESS = RGBColor(0x4A, 0x55, 0x68)
COLOR_ACCENT = RGBColor(0xD2, 0x26, 0x30)
COLOR_SEPARATOR = RGBColor(0xE2, 0xE8, 0xF0)
COLOR_TABLE_HEADER_BG = "F7FAFC"
COLOR_TABLE_ROW_BG = "F8FAFC"


def set_cell_background(cell, hex_color: str):
    """Устанавливает цвет фона ячейки таблицы."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)


def hex_to_rgb(hex_color: str):
    """Преобразует HEX в RGBColor."""
    hex_color = hex_color.lstrip('#')
    try:
        return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    except:
        return 27, 54, 93


def format_model_description(model: dict) -> str:
    """Формирует описание модели."""
    if model.get("description"):
        return model["description"]
    parts = []
    if model.get("manufacturer"):
        parts.append(f"Производитель: {model['manufacturer']}")
    if model.get("series"):
        parts.append(f"Серия/тип: {model['series']}")
    return "; ".join(parts) if parts else "Сплит-система настенного типа"


def generate_docx(variants: list, customer_data: dict, filename: str):
    """Основная функция генерации DOCX."""
    settings = config.load_settings()
    logo_path = settings.get("logo_path", "").strip()
    primary_hex = settings.get("primary_color", "#1B365D")
    font_name = settings.get("font_family", "Segoe UI")
    logo_width_cm = float(settings.get("logo_width", 3.0))

    doc = Document()
    style = doc.styles['Normal']
    style.font.name = font_name

    # Настройка полей документа
    for section in doc.sections:
        section.left_margin = Cm(1.9)
        section.right_margin = Cm(1.9)
        section.top_margin = Cm(1.9)
        section.bottom_margin = Cm(1.9)

    # ==================== ШАПКА ====================
    header_table = doc.add_table(rows=2, cols=2)
    header_table.autofit = False
    header_table.columns[0].width = Cm(11.5)
    header_table.columns[1].width = Cm(5.7)

    # Левая часть шапки
    left_cell = header_table.cell(0, 0)
    left_cell.text = settings.get("activity", "КОНДИЦИОНЕРЫ\nВЕНТИЛЯЦИЯ\nОТОПЛЕНИЕ")
    for para in left_cell.paragraphs:
        if para.runs:
            run = para.runs[0]
            run.bold = True
            run.font.size = Pt(13)
            run.font.color.rgb = COLOR_SUBTITLE
            run.font.name = font_name

    # Правая часть — логотип или название
    right_top = header_table.cell(0, 1)
    right_top.text = ""
    p = right_top.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    if logo_path and os.path.exists(logo_path):
        run_img = p.add_run()
        run_img.add_picture(logo_path, width=Cm(logo_width_cm))
    else:
        run_neva = p.add_run("НЕВА")
        run_neva.bold = True
        run_neva.font.size = Pt(18)
        run_neva.font.color.rgb = RGBColor(*hex_to_rgb(primary_hex))
        run_neva.font.name = font_name

        run_con = p.add_run("КОН")
        run_con.bold = True
        run_con.font.size = Pt(18)
        run_con.font.color.rgb = COLOR_ACCENT
        run_con.font.name = font_name

    # Адрес
    right_bottom = header_table.cell(1, 1)
    right_bottom.text = settings.get("address", "г. СПб, Детский пер., д. 5")
    run_addr = right_bottom.paragraphs[0].runs[0]
    run_addr.font.size = Pt(9.5)
    run_addr.font.color.rgb = COLOR_ADDRESS
    run_addr.font.name = font_name
    right_bottom.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Разделитель
    p_line = doc.add_paragraph()
    p_line.paragraph_format.space_before = Pt(5)
    p_line.paragraph_format.space_after = Pt(10)
    run_line = p_line.add_run("—" * 90)
    run_line.font.color.rgb = RGBColor(*hex_to_rgb(primary_hex))
    run_line.font.name = font_name

    # Контакты
    p_contacts = doc.add_paragraph()
    run_c = p_contacts.add_run(settings.get("contacts", ""))
    run_c.font.size = Pt(9.5)
    run_c.font.color.rgb = COLOR_ADDRESS
    run_c.font.name = font_name

    p_web = doc.add_paragraph()
    run_w = p_web.add_run(settings.get("website", ""))
    run_w.font.size = Pt(9.5)
    run_w.bold = True
    run_w.font.color.rgb = RGBColor(*hex_to_rgb(primary_hex))
    run_w.font.name = font_name

    p_serv = doc.add_paragraph()
    run_s = p_serv.add_run(settings.get("services", ""))
    run_s.font.size = Pt(9.5)
    run_s.font.italic = True
    run_s.font.color.rgb = COLOR_SUBTITLE
    run_s.font.name = font_name

    doc.add_paragraph()

    # ==================== РЕКВИЗИТЫ ====================
    info_table = doc.add_table(rows=5, cols=2)
    info_table.style = 'Table Grid'
    info_table.columns[0].width = Cm(3.0)
    info_table.columns[1].width = Cm(14.0)

    date_str = customer_data.get("date", datetime.now().strftime("%d.%m.%Y"))
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        date_str = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")

    rows_data = [
        ("Дата:", date_str),
        ("Тел./факс:", customer_data.get("phone", "")),
        ("Кому:", customer_data.get("to", "")),
        ("От:", customer_data.get("from", "")),
        ("Объект:", customer_data.get("object", ""))
    ]

    for i, (label, value) in enumerate(rows_data):
        # Метка
        cell_lbl = info_table.cell(i, 0)
        cell_lbl.text = label
        run_lbl = cell_lbl.paragraphs[0].runs[0]
        run_lbl.bold = True
        run_lbl.font.color.rgb = RGBColor(*hex_to_rgb(primary_hex))
        run_lbl.font.name = font_name
        set_cell_background(cell_lbl, COLOR_TABLE_HEADER_BG)

        # Значение
        cell_val = info_table.cell(i, 1)
        cell_val.text = value
        cell_val.paragraphs[0].runs[0].font.name = font_name

    doc.add_paragraph()

    # Заголовок документа
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title_para.add_run("КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ")
    run.bold = True
    run.underline = True
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(*hex_to_rgb(primary_hex))
    run.font.name = font_name

    doc.add_paragraph()

    intro = doc.add_paragraph(
        "Благодарим Вас за обращение в нашу фирму по вопросам вентиляции и "
        "кондиционирования воздуха. Для создания комфортных температурных условий "
        "в Вашем помещении предлагаем установить следующий вид кондиционеров:"
    )
    intro.runs[0].font.name = font_name
    doc.add_paragraph()

    # ==================== ВАРИАНТЫ ====================
    models = config.load_models()

    for idx, var in enumerate(variants, 1):
        m_key = var["model_key"]
        model = models.get(m_key)
        if not model:
            raise Exception(f"Модель '{m_key}' не найдена в базе данных.")

        # Заголовок варианта
        h2 = doc.add_paragraph(f"{idx} вариант")
        h2.paragraph_format.space_before = Pt(10)
        h2.paragraph_format.space_after = Pt(2)
        run_h2 = h2.runs[0]
        run_h2.font.size = Pt(13)
        run_h2.bold = True
        run_h2.font.color.rgb = RGBColor(*hex_to_rgb(primary_hex))
        run_h2.font.name = font_name

        # Описание
        desc_text = format_model_description(model)
        p_desc = doc.add_paragraph()
        p_desc.paragraph_format.space_after = Pt(6)
        run_desc = p_desc.add_run(desc_text)
        run_desc.font.size = Pt(10.5)
        run_desc.font.italic = True
        run_desc.font.color.rgb = COLOR_ADDRESS
        run_desc.font.name = font_name

        # Таблица характеристик
        table = doc.add_table(rows=2, cols=9)
        table.style = 'Table Grid'
        col_widths = [Cm(2.5), Cm(1.5), Cm(1.8), Cm(1.8), Cm(1.8), Cm(2.2), Cm(1.2), Cm(1.8), Cm(2.2)]
        for row in table.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = w

        headers = [
            "Модель", "Уровень шума, дБ", "Произв. по холоду, кВт",
            "Произв. по теплу, кВт", "Потреб. мощн., кВт",
            "Габариты внутр. блока, мм", "Кол-во, шт.", "Цена, руб.", "Итого, руб."
        ]

        # Заголовки таблицы
        for i, h in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = h
            run_h = cell.paragraphs[0].runs[0]
            run_h.bold = True
            run_h.font.size = Pt(8.5)
            run_h.font.color.rgb = RGBColor(255, 255, 255)
            run_h.font.name = font_name
            set_cell_background(cell, primary_hex.replace('#', ''))
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        # Данные
        qty = var["quantity"]
        price = model.get("price", 0)
        total_equip = price * qty

        row = table.rows[1]
        values = [
            m_key,
            model.get("noise_level", ""),
            model.get("cooling_kw", ""),
            model.get("heating_kw", ""),
            model.get("power_kw", ""),
            model.get("dimensions", ""),
            str(qty),
            f"{price:,}".replace(",", " "),
            f"{total_equip:,}".replace(",", " ")
        ]

        for i, val in enumerate(values):
            cell = row.cells[i]
            cell.text = val
            run = cell.paragraphs[0].runs[0]
            run.font.size = Pt(8.5)
            run.font.name = font_name
            set_cell_background(cell, COLOR_TABLE_ROW_BG)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        doc.add_paragraph()

        # Дополнительные расходы
        tab_pos = Cm(17.27)
        for label, value in [
            ("Монтаж кондиционера", var.get("installation_price", 0)),
            ("Согласование места размещения наружного блока", var.get("approval_price", 0))
        ]:
            p = doc.add_paragraph()
            p.paragraph_format.tab_stops.add_tab_stop(tab_pos, WD_TAB_ALIGNMENT.RIGHT)
            run_lbl = p.add_run(label)
            run_lbl.bold = True
            run_lbl.font.name = font_name
            p.add_run(f"\t{value:,} руб.".replace(",", " "))

        # Итого по варианту
        total = total_equip + var.get("installation_price", 0) + var.get("approval_price", 0)
        p = doc.add_paragraph()
        p.paragraph_format.tab_stops.add_tab_stop(tab_pos, WD_TAB_ALIGNMENT.RIGHT)
        run_tot = p.add_run("ИТОГО")
        run_tot.bold = True
        run_tot.font.size = Pt(11)
        run_tot.font.color.rgb = COLOR_ACCENT
        run_tot.font.name = font_name
        p.add_run(f"\t{total:,} руб.".replace(",", " ")).bold = True

        # Разделитель
        p_sep = doc.add_paragraph()
        p_sep.paragraph_format.space_before = Pt(8)
        p_sep.paragraph_format.space_after = Pt(8)
        run_sep = p_sep.add_run("—" * 90)
        run_sep.font.color.rgb = COLOR_SEPARATOR
        run_sep.font.name = font_name

    # ==================== ПОДПИСЬ ====================
    doc.add_paragraph()
    p_respect = doc.add_paragraph("С уважением,")
    p_respect.runs[0].font.name = font_name

    p_sig = doc.add_paragraph()
    run_sig = p_sig.add_run(settings.get("manager_signature", "Толстиков Игорь."))
    run_sig.bold = True
    run_sig.font.color.rgb = RGBColor(*hex_to_rgb(primary_hex))
    run_sig.font.name = font_name

    try:
        doc.save(filename)
    except PermissionError:
        raise PermissionError(f"Файл '{os.path.basename(filename)}' открыт в Word. Закройте его и попробуйте снова.")