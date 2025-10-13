# app/utils/formatting.py

from typing import Dict, Any

def format_section_output(data: Dict[str, Any], json_schema: Dict[str, Any]) -> str:
    formatted_content = []
    
    # 使用 schema 的 properties 字段进行格式化
    if 'properties' in json_schema:
        for key, prop_info in json_schema['properties'].items():
            if key in data:
                title = prop_info.get('title', key.replace('_', ' ').title())
                description = prop_info.get('description', '')
                value = data[key]

                section_text = f"**{description if description else title}**\n"
                
                if isinstance(value, list):
                    list_text = []
                    item_schema_props = prop_info.get("items", {}).get("properties", {})
                    for i, item in enumerate(value, start=1):
                        if isinstance(item, dict):
                            item_lines = [f"{i}. {item.get('name', f'项目{i}')}".strip()]
                            for sub_key, sub_val in item.items():
                                if sub_key == "name": continue
                                sub_title = item_schema_props.get(sub_key, {}).get("description", sub_key)
                                item_lines.append(f"   - {sub_title}：{sub_val}")
                            list_text.append("\n".join(item_lines))
                        else:
                            list_text.append(f"{i}. {item}")
                    value_text = "\n".join(list_text)
                elif isinstance(value, dict):
                    value_text = "\n".join(f"- {k}：{v}" for k, v in value.items())
                else:
                    value_text = str(value)
                
                section_text += f"{value_text}\n"
                formatted_content.append(section_text)
    else:
        # 如果 schema 没有 properties 字段，则通用处理
        for key, value in data.items():
            title = key.replace('_', ' ').title()
            if isinstance(value, list):
                list_text = "\n".join(f"- {v}" for v in value)
                formatted_content.append(f"**{title}**\n{list_text}\n")
            else:
                formatted_content.append(f"**{title}**\n{value}\n")

    return "\n".join(formatted_content)
