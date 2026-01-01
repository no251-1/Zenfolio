"""
星级评分组件
支持鼠标悬停和点击选择
"""
import streamlit as st
import streamlit.components.v1 as components

def star_rating(key: str, max_stars: int = 5, default: int = 0, star_size: str = "30px"):
    """
    创建星级评分组件
    
    参数:
        key: 唯一标识符
        max_stars: 最大星级数（默认5）
        default: 默认选中的星级（0-5）
        star_size: 星星大小（CSS格式，如"30px"）
    
    返回:
        选中的星级数（0-5）
    """
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .star-rating {{
                display: flex;
                flex-direction: row-reverse;
                justify-content: flex-end;
                gap: 5px;
                font-size: {star_size};
                cursor: pointer;
                user-select: none;
            }}
            .star-rating input {{
                display: none;
            }}
            .star-rating label {{
                color: #ddd;
                cursor: pointer;
                transition: color 0.2s;
            }}
            .star-rating label:hover,
            .star-rating label:hover ~ label {{
                color: #ffc107;
            }}
            .star-rating input:checked ~ label {{
                color: #ffc107;
            }}
            .star-rating input:checked ~ label ~ label {{
                color: #ffc107;
            }}
            .star-rating:hover label {{
                color: #ffc107;
            }}
            .star-rating:not(:hover) input:checked ~ label {{
                color: #ffc107;
            }}
            .star-rating:not(:hover) input:not(:checked) ~ label {{
                color: #ddd;
            }}
        </style>
    </head>
    <body>
        <div class="star-rating" id="star-rating-{key}">
            <input type="radio" name="rating-{key}" value="5" id="star5-{key}" {'checked' if default == 5 else ''}>
            <label for="star5-{key}">⭐</label>
            <input type="radio" name="rating-{key}" value="4" id="star4-{key}" {'checked' if default == 4 else ''}>
            <label for="star4-{key}">⭐</label>
            <input type="radio" name="rating-{key}" value="3" id="star3-{key}" {'checked' if default == 3 else ''}>
            <label for="star3-{key}">⭐</label>
            <input type="radio" name="rating-{key}" value="2" id="star2-{key}" {'checked' if default == 2 else ''}>
            <label for="star2-{key}">⭐</label>
            <input type="radio" name="rating-{key}" value="1" id="star1-{key}" {'checked' if default == 1 else ''}>
            <label for="star1-{key}">⭐</label>
            <input type="radio" name="rating-{key}" value="0" id="star0-{key}" {'checked' if default == 0 else ''} style="display:none;">
        </div>
        <script>
            (function() {{
                const ratingDiv = document.getElementById('star-rating-{key}');
                const inputs = ratingDiv.querySelectorAll('input[type="radio"]');
                
                // 监听选择变化
                inputs.forEach(input => {{
                    input.addEventListener('change', function() {{
                        const value = this.value;
                        // 发送消息到Streamlit
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: parseInt(value)
                        }}, '*');
                    }});
                }});
                
                // 悬停效果
                ratingDiv.addEventListener('mouseleave', function() {{
                    const checked = ratingDiv.querySelector('input:checked');
                    if (checked) {{
                        const value = parseInt(checked.value);
                        inputs.forEach((input, index) => {{
                            const label = input.nextElementSibling;
                            if (5 - index <= value) {{
                                label.style.color = '#ffc107';
                            }} else {{
                                label.style.color = '#ddd';
                            }}
                        }});
                    }}
                }});
            }})();
        </script>
    </body>
    </html>
    """
    
    # 使用streamlit组件渲染HTML
    selected_rating = components.html(
        html_code,
        height=50,
        key=key
    )
    
    # 如果组件返回None，使用默认值
    if selected_rating is None:
        return default
    
    return selected_rating if isinstance(selected_rating, int) else default

