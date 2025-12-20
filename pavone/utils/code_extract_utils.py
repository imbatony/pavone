"""
尝试从文件名或者keywords或者标题中提取编号代码
"""

import re
from typing import Optional

ignore_regrex = r"\w+2048\.com|Carib(?:beancom)?|[^a-z\d](?:f?hd|lt)[^a-z\d]"
fc2_regrex = r"fc2[^a-z\d]{0,5}(ppv[^a-z\d]{0,5})?(\d{5,7})"
heydouga_regrex = r"(heydouga)[-_]*(\d{4})[-_]0?(\d{3,5})"
hey_regex = r"(hey)[-_]*(\d{4})[-_]0?(\d{3,5})"
heyzo_regex = r"(heyzo)[-_]?(\d{3,5})"
no_domian_regrex = r"\w+\d*\.(com|net|app|xyz|vip)"
special_regrex_1 = r"(red[01]\d{2}|sky[0-3]\d{2}|ex0*0(?:0\d|\d0?))"
n_series_regex = r"(n\d{4}|k\d{4})"
normal_regrex = r"([a-zA-Z]{2,5})[-_](\d{2,5})"
normal_regrex_2 = r"([a-zA-Z]{2,5})(\d{2,5})"
tma_regrex = r"(T28)([-_]?)(\d{3})"
pure_number_regrex = r"(\d{6}[-_]\d{3})"
carib_regrex = r"(\d{6})[-_](\d{3})(?:-carib)?"


class CodeExtractUtils:
    @staticmethod
    def extract_code_from_text(original_text: str) -> Optional[str]:
        """
        从文本中提取编号代码
        """
        # 如果文本为空，返回空字符串
        if not original_text:
            return ""

        # 去除忽略的正则表达式
        original_text = re.sub(ignore_regrex, "", original_text, flags=re.IGNORECASE)
        # 先统一改为小写
        text = original_text.lower()
        # 去除domain
        text = re.sub(no_domian_regrex, "", text)

        # 去除')(' 后重新尝试匹配
        if ")(" in text:
            text = text.replace(")(", "-")

        # fc2识别
        if "fc2" in text:
            # 根据FC2 Club的影片数据，FC2编号为5-7个数字
            if match := re.search(fc2_regrex, text, re.IGNORECASE):
                return "FC2-" + match.group(2)

        # heyzo识别
        if "heyzo" in text:
            if match := re.search(heyzo_regex, text, re.IGNORECASE):
                return "Heyzo-" + match.group(2)

        # heydouga识别
        if "heydouga" in text:
            if match := re.search(heydouga_regrex, text, re.IGNORECASE):
                return "Heydouga-" + match.group(2) + "-" + match.group(3)

        # hey识别, 匹配缩写成hey的heydouga影片。由于番号分三部分，要先于后面分两部分的进行匹配
        if "hey" in text and ("hey-" in text or "hey_" in text):
            if match := re.search(hey_regex, text, re.IGNORECASE):
                return "Heydouga-" + match.group(2) + "-" + match.group(3)

        # TMA番号识别
        if "t28" in text:
            if match := re.search(tma_regrex, text, re.IGNORECASE):
                return match.group(1).upper() + "-" + match.group(3)

        # Try to match Tokyo-hot n, k series
        if "n" in text:
            if match := re.search(n_series_regex, text, re.IGNORECASE):
                return match.group(1).lower()

        # 运行到这里时表明无法匹配到带分隔符的番号, 先尝试匹配东热的red, sky, ex三个不带-分隔符的系列
        # RED100=> RED100
        # SKY001=> SKY001
        # EX001=> EX001
        if match := re.search(special_regrex_1, text, re.IGNORECASE):
            return match.group(1).upper()

        # 普通番号，优先尝试匹配带分隔符的（如ABC-123）
        if match := re.search(normal_regrex, text, re.IGNORECASE):
            # 返回带分隔符的番号
            return match.group(1).upper() + "-" + match.group(2)

        # 再将影片视作缺失了-分隔符来匹配
        if match := re.search(normal_regrex_2, text, re.IGNORECASE):
            return match.group(1).upper() + "-" + match.group(2)

        # 纯数字编号识别
        if match := re.search(pure_number_regrex, text, re.IGNORECASE):
            return match.group(1).upper()

        # 如果没有匹配到任何编号，返回None
        return None
