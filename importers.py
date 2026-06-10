# -*- coding: utf-8 -*-
import os
import re
import json
import pandas as pd
import pdfplumber
import config

# Глобальные синонимы (базовый набор)
SYNONYMS = {
    'Модель': ['модель', 'наименование', 'код', 'model', 'name', 'марка', 'внутренний блок', 'индекс', 'оборудование', 'аппарат'],
    'Шум': ['шум', 'уровень шума', 'звуков', 'дба', 'дб', 'noise', 'dba', 'db', 'звук', 'давление'],
    'Холод': ['холод', 'охлажд', 'cool', 'произв. по хол', 'хладопроизв', 'производительность по холоду'],
    'Тепло': ['тепло', 'обогрев', 'heat', 'произв. по теп', 'теплопроизв', 'производительность по теплу'],
    'Мощность': ['мощность', 'потреб', 'power', 'потребл', 'потребление', 'электр'],
    'Габариты': ['габарит', 'размер', 'шхгхв', 'шхвхг', 'dimension', 'width', 'размеры', 'габаритные размеры'],
    'Цена': ['цена', 'стоимость', 'price', 'розн', 'руб', 'руб.', 'rub', 'прайс', 'рц']
}

OPTIONAL_SYNONYMS = {
    'manufacturer': ['производитель', 'бренд', 'brand', 'марка', 'фирма', 'vendor'],
    'series': ['серия', 'тип', 'категория', 'category', 'family', 'line', 'модельный ряд', 'линейка'],
    'description': ['описание', 'детали', 'detail', 'comments', 'комментарий', 'наименование', 'характеристики']
}

# Кэш для профилей брендов
_BRAND_PROFILES_CACHE = None

def load_brand_profiles():
    """Загружает профили брендов из JSON."""
    global _BRAND_PROFILES_CACHE
    
    if _BRAND_PROFILES_CACHE is not None:
        return _BRAND_PROFILES_CACHE
    
    profile_path = os.path.join(os.path.dirname(__file__), 'brand_profiles.json')
    
    if not os.path.exists(profile_path):
        _BRAND_PROFILES_CACHE = {"brands": {}, "global_synonyms": {}}
        return _BRAND_PROFILES_CACHE
    
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            _BRAND_PROFILES_CACHE = json.load(f)
            return _BRAND_PROFILES_CACHE
    except Exception:
        _BRAND_PROFILES_CACHE = {"brands": {}, "global_synonyms": {}}
        return _BRAND_PROFILES_CACHE

def clear_brand_cache():
    """Сбрасывает кеш профилей, чтобы при следующем обращении они загрузились заново."""
    global _BRAND_PROFILES_CACHE
    _BRAND_PROFILES_CACHE = None

def detect_brand_from_file(df):
    """Детектирует бренд по содержимому файла (модели, описание)."""
    profiles = load_brand_profiles()
    if not profiles.get('brands'):
        return None
    
    # Собираем образец данных из первых строк
    sample_values = []
    for val in df.iloc[:5].values.flatten():
        if pd.isna(val):
            sample_values.append('')
        else:
            sample_values.append(str(val))
    sample_text = ' '.join(sample_values).lower()
    
    # Ищем совпадения по алиасам
    for brand_key, brand_info in profiles['brands'].items():
        for alias in brand_info.get('aliases', []):
            if alias.lower() in sample_text:
                return brand_key
    
    return None

def detect_brand_by_headers(headers, required_fields):
    """
    Пытается определить бренд, проверяя, для какого профиля
    все обязательные поля могут быть найдены по брендовым синонимам.
    Возвращает brand_key или None.
    """
    profiles = load_brand_profiles()
    if not profiles.get('brands'):
        return None
    candidates = []
    for brand_key, brand_info in profiles['brands'].items():
        col_syns = brand_info.get('column_synonyms', {})
        ok = True
        for field in required_fields:
            syns = col_syns.get(field, [])
            found = False
            for h in headers:
                h_lower = str(h).strip().lower()
                for syn in syns:
                    if syn.lower() in h_lower:
                        found = True
                        break
                if found:
                    break
            if not found:
                ok = False
                break
        if ok:
            candidates.append(brand_key)
    
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        raise Exception(
            f"По заголовкам найдено несколько подходящих профилей брендов: {', '.join(candidates)}.\n"
            f"Добавьте уникальные алиасы в файл или выберите бренд вручную."
        )
    return None

def get_synonyms_for_field(field_name, brand_key=None):
    """
    Получает синонимы для поля. Если задан бренд и в его профиле есть синонимы для этого поля,
    используются ТОЛЬКО брендовые синонимы (глобальные игнорируются).
    Иначе используются только глобальные.
    """
    profiles = load_brand_profiles()
    brand_syns = []
    
    if brand_key and brand_key in profiles.get('brands', {}):
        brand_syns = profiles['brands'][brand_key].get('column_synonyms', {}).get(field_name, [])
    
    if brand_syns:
        seen = set()
        unique = []
        for s in brand_syns:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique.append(s)
        return unique
    
    global_syns = SYNONYMS.get(field_name, [])
    seen = set()
    unique = []
    for s in global_syns:
        if s.lower() not in seen:
            seen.add(s.lower())
            unique.append(s)
    return unique

def find_column_by_synonyms(headers, field_name, brand_key=None):
    """Ищет колонку по словарю синонимов с учетом профиля бренда."""
    synonyms = get_synonyms_for_field(field_name, brand_key)
    
    # 1. Точное совпадение заголовка с любым из синонимов (без учёта регистра)
    for h in headers:
        h_lower = str(h).strip().lower()
        for syn in synonyms:
            if h_lower == syn.lower():
                return h
    
    # 2. Поиск по синонимам как подстрокам
    for h in headers:
        h_lower = str(h).strip().lower()
        for syn in synonyms:
            if syn.lower() in h_lower:
                # Защита от перепутывания для глобальных синонимов
                if not brand_key:
                    if field_name == 'Холод' and any(x in h_lower for x in ['тепло', 'обогрев', 'heat', 'тепл']):
                        continue
                    if field_name == 'Тепло' and any(x in h_lower for x in ['холод', 'охлажд', 'cool', 'хол']):
                        continue
                    if field_name in ['Холод', 'Тепло'] and any(x in h_lower for x in ['потреб', 'consumption', 'power', 'потребл']):
                        continue
                return h
    return None

def find_optional_column(headers, field_name):
    for h in headers:
        if str(h).strip().lower() == field_name.lower():
            return h
    for h in headers:
        h_lower = str(h).strip().lower()
        for syn in OPTIONAL_SYNONYMS[field_name]:
            if syn in h_lower:
                return h
    return None

def parse_price(price_str):
    if not price_str:
        return 0
    price_str = str(price_str).strip()
    if price_str.lower() in ['nan', 'none', '']:
        return 0
        
    match = re.search(r'\d[\d.,\s]*\d|\d', price_str)
    if not match:
        return 0
        
    clean = match.group(0)
    clean = re.sub(r'\s+', '', clean)
    
    if '.' in clean and ',' in clean:
        if clean.find('.') < clean.find(','):
            clean = clean.replace('.', '')
        else:
            clean = clean.replace(',', '')
        clean = clean.replace(',', '.')
    elif ',' in clean:
        if re.search(r',\d{2}$', clean):
            clean = clean.replace(',', '.')
        else:
            clean = clean.replace(',', '')
    elif '.' in clean:
        if clean.count('.') > 1:
            clean = clean.replace('.', '')
        elif re.search(r'\.\d{3}$', clean):
            clean = clean.replace('.', '')
            
    clean = clean.strip('.')
    
    try:
        if '.' in clean:
            return int(float(clean))
        else:
            return int(clean) if clean else 0
    except Exception:
        return 0

def safe_str(val, default=''):
    """Преобразует значение в строку, заменяя NaN/None на default."""
    if pd.isna(val) or val is None:
        return default
    return str(val).strip()

def import_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext in ['.xlsx', '.xls']:
        df = pd.read_excel(filepath)
    elif ext == '.csv':
        df = pd.read_csv(filepath, encoding='utf-8')
    else:
        raise Exception("Формат файла не поддерживается. Разрешены только Excel (*.xlsx, *.xls) и CSV.")
        
    df.columns = [str(c).strip() for c in df.columns]
    
    required = ['Модель', 'Шум', 'Холод', 'Тепло', 'Мощность', 'Габариты', 'Цена']
    
    # Автоматически детектируем бренд по содержимому
    detected_brand = detect_brand_from_file(df)
    
    # Если не получилось – пробуем определить по заголовкам
    if detected_brand is None:
        try:
            detected_brand = detect_brand_by_headers(df.columns, required)
        except Exception as e:
            raise Exception(f"Не удалось определить бренд. {str(e)}")
    
    # Интеллектуальный поиск колонок с учетом профиля бренда
    col_map = {}
    for req in required:
        found = find_column_by_synonyms(df.columns, req, detected_brand)
        if found is None:
            synonyms_list = get_synonyms_for_field(req, detected_brand)
            raise Exception(
                f"Не удалось автоматически распознать колонку '{req}' в файле.\n"
                f"Пожалуйста, назовите колонку одним из синонимов: {', '.join(synonyms_list[:5])}...\n"
                f"Доступные колонки в файле: {', '.join(df.columns)}"
            )
        col_map[req] = found
        
    # Ищем необязательное описание/серию
    desc_col = None
    for c in df.columns:
        if 'описание' in c.lower() or 'серия' in c.lower() or 'детали' in c.lower() or 'тип' in c.lower() or 'наименование' in c.lower():
            desc_col = c
            break
    manufacturer_col = find_optional_column(df.columns, 'manufacturer')
    series_col = find_optional_column(df.columns, 'series')
    description_col = desc_col or find_optional_column(df.columns, 'description')
    
    models = config.load_models()
    count = 0
    skipped_empty_model = 0
    skipped_bad_price = 0
    
    for _, row in df.iterrows():
        try:
            key = safe_str(row[col_map['Модель']])
            if not key or key.lower() in ['nan', 'none', '']:
                skipped_empty_model += 1
                continue
                
            price_val = parse_price(row[col_map['Цена']])
            if price_val <= 0:
                skipped_bad_price += 1
                continue
                
            desc_parts = []
            if description_col and pd.notna(row[description_col]):
                desc_parts.append(safe_str(row[description_col]))
            else:
                if manufacturer_col and pd.notna(row[manufacturer_col]):
                    desc_parts.append(safe_str(row[manufacturer_col]))
                if series_col and pd.notna(row[series_col]):
                    desc_parts.append(safe_str(row[series_col]))
            
            desc_val = "; ".join(desc_parts) if desc_parts else "Сплит-система настенного типа"
            
            model_data = {
                "description": desc_val,
                "noise_level": safe_str(row[col_map['Шум']]),
                "cooling_kw": safe_str(row[col_map['Холод']]),
                "heating_kw": safe_str(row[col_map['Тепло']]),
                "power_kw": safe_str(row[col_map['Мощность']]),
                "dimensions": safe_str(row[col_map['Габариты']]),
                "price": price_val
            }
            if manufacturer_col and pd.notna(row[manufacturer_col]):
                model_data["manufacturer"] = safe_str(row[manufacturer_col])
            if series_col and pd.notna(row[series_col]):
                model_data["series"] = safe_str(row[series_col])
            if detected_brand:
                model_data["brand"] = detected_brand
            
            models[key] = model_data
            count += 1
        except Exception:
            continue
            
    if count == 0:
        details = []
        details.append(f"Всего строк в файле: {len(df)}")
        details.append(f"Найденные колонки: {col_map}")
        details.append(f"Бренд: {detected_brand or 'не определён'}")
        details.append(f"Строк с пустой моделью: {skipped_empty_model}")
        details.append(f"Строк с ценой <= 0 или нечитаемой: {skipped_bad_price}")
        if skipped_bad_price > 0 and col_map.get('Цена'):
            sample_price = safe_str(df[col_map['Цена']].iloc[0])
            details.append(f"Пример значения цены в первой строке: '{sample_price}'")
        raise Exception(
            "В файле не найдено корректных строк для импорта.\n" +
            "\n".join(details)
        )
        
    config.save_models(models)
    brand_info = f" (бренд: {detected_brand})" if detected_brand else ""
    return f"{count} моделей{brand_info}"

def import_from_pdf(filepath):
    all_rows = []
    required = ['Модель', 'Шум', 'Холод', 'Тепло', 'Мощность', 'Габариты', 'Цена']
    detected_brand = None
    
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                    
                headers = [str(c).strip() if c else '' for c in table[0]]
                
                if detected_brand is None:
                    try:
                        detected_brand = detect_brand_by_headers(headers, required)
                    except Exception:
                        pass
                
                col_idx = {}
                for req in required:
                    found = find_column_by_synonyms(headers, req, detected_brand)
                    if found is None:
                        break
                    col_idx[req] = headers.index(found)
                else:
                    desc_idx = None
                    for i, h in enumerate(headers):
                        if any(x in h.lower() for x in ['описание', 'серия', 'название', 'тип', 'категория']):
                            desc_idx = i
                            break
                    manufacturer_idx = None
                    series_idx = None
                    for i, h in enumerate(headers):
                        h_lower = h.lower()
                        if manufacturer_idx is None and any(x in h_lower for x in OPTIONAL_SYNONYMS['manufacturer']):
                            manufacturer_idx = i
                        if series_idx is None and any(x in h_lower for x in OPTIONAL_SYNONYMS['series']):
                            series_idx = i
                    
                    for row in table[1:]:
                        if not any(row):
                            continue
                        try:
                            model = safe_str(row[col_idx['Модель']])
                            if not model or model.lower() in ['nan', 'none', '']:
                                continue
                                
                            price_val = parse_price(row[col_idx['Цена']])
                            if price_val <= 0:
                                continue
                                
                            desc_parts = []
                            if desc_idx is not None and row[desc_idx]:
                                desc_parts.append(safe_str(row[desc_idx]))
                            else:
                                if manufacturer_idx is not None and row[manufacturer_idx]:
                                    desc_parts.append(safe_str(row[manufacturer_idx]))
                                if series_idx is not None and row[series_idx]:
                                    desc_parts.append(safe_str(row[series_idx]))
                            
                            desc_val = "; ".join(desc_parts) if desc_parts else "Сплит-система настенного типа"
                            
                            row_data = {
                                'Модель': model,
                                'description': desc_val,
                                'Шум': safe_str(row[col_idx['Шум']]),
                                'Холод': safe_str(row[col_idx['Холод']]),
                                'Тепло': safe_str(row[col_idx['Тепло']]),
                                'Мощность': safe_str(row[col_idx['Мощность']]),
                                'Габариты': safe_str(row[col_idx['Габариты']]),
                                'Цена': price_val
                            }
                            if manufacturer_idx is not None and row[manufacturer_idx]:
                                row_data['manufacturer'] = safe_str(row[manufacturer_idx])
                            if series_idx is not None and row[series_idx]:
                                row_data['series'] = safe_str(row[series_idx])
                            all_rows.append(row_data)
                        except Exception:
                            continue
                            
    if not all_rows:
        raise Exception("В PDF-файле не найдены подходящие таблицы с нужными колонками (Модель, Шум, Холод, Тепло, Мощность, Габариты, Цена)")
        
    models = config.load_models()
    for r in all_rows:
        model_data = {
            "description": r['description'],
            "noise_level": r['Шум'],
            "cooling_kw": r['Холод'],
            "heating_kw": r['Тепло'],
            "power_kw": r['Мощность'],
            "dimensions": r['Габариты'],
            "price": r['Цена']
        }
        if 'manufacturer' in r:
            model_data['manufacturer'] = r['manufacturer']
        if 'series' in r:
            model_data['series'] = r['series']
        if detected_brand:
            model_data['brand'] = detected_brand
        models[r['Модель']] = model_data
        
    config.save_models(models)
    brand_info = f" (бренд: {detected_brand})" if detected_brand else ""
    return f"{len(all_rows)} моделей{brand_info}"