import re

class VietnameseTextNormalizer:
    def __init__(self):
        # Mapping for Vietnamese numbers
        self.numbers_dict = {
            '0': 'không',
            '1': 'một',
            '2': 'hai',
            '3': 'ba',
            '4': 'bốn',
            '5': 'năm',
            '6': 'sáu',
            '7': 'bảy',
            '8': 'tám',
            '9': 'chín',
            '10': 'mười'
        }
        
        # Dictionary for units in Vietnamese
        self.units = [
            '', 'nghìn', 'triệu', 'tỷ', 'nghìn tỷ', 'triệu tỷ', 'tỷ tỷ'
        ]

        # Month names in Vietnamese
        self.month_names = {
            '01': 'một', '1': 'một',
            '02': 'hai', '2': 'hai',
            '03': 'ba', '3': 'ba',
            '04': 'tư', '4': 'tư',
            '05': 'năm', '5': 'năm',
            '06': 'sáu', '6': 'sáu',
            '07': 'bảy', '7': 'bảy',
            '08': 'tám', '8': 'tám',
            '09': 'chín', '9': 'chín',
            '10': 'mười',
            '11': 'mười một',
            '12': 'mười hai'
        }

    def normalize(self, text):
        """
        Normalize Vietnamese text for text-to-speech input.
        
        Args:
            text (str): Input text to normalize
        
        Returns:
            str: Normalized text
        """
        if not text:
            return ""
        
        # Remove extra whitespaces, tabs, newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Separate mixed alphanumeric strings
        text = self._separate_alphanumeric(text).replace('-', ' ').replace('_', ' ')
        
        # Convert date-time formats (YYYY-MM-DD HH:MM:SS)
        text = re.sub(
            r'(\d{4})-(\d{1,2})-(\d{1,2}) (\d{1,2}):(\d{1,2}):(\d{1,2})', 
            lambda match: self._convert_datetime(match.group(1), match.group(2), match.group(3), 
                                               match.group(4), match.group(5), match.group(6)), 
            text
        )
        
        # Convert dates (DD/MM/YYYY format with / separator)
        text = re.sub(
            r'(\d{1,2})\/(\d{1,2})\/(\d{4})', 
            lambda match: self._convert_date(match.group(1), match.group(2), match.group(3), day_first=True), 
            text
        )
        
        # Convert dates (DD-MM-YYYY format with - separator)
        text = re.sub(
            r'(\d{1,2})-(\d{1,2})-(\d{4})', 
            lambda match: self._convert_date(match.group(1), match.group(2), match.group(3), day_first=True), 
            text
        )
        
        # Convert dates (YYYY-MM-DD format with - separator)
        
        text = re.sub(
            r'(\d{4})-(\d{1,2})-(\d{1,2})', 
            lambda match: self._convert_date(match.group(3), match.group(2), match.group(1), day_first=False), 
            text
        )
        
        # Convert decimal numbers (using comma as decimal separator)
        text = re.sub(
            r'\b(\d+),(\d+)\b', 
            lambda match: self._convert_decimal_number(match.group(1), match.group(2)),
            text
        )
        
        # Convert decimal numbers (using period as decimal separator)
        text = re.sub(
            r'\b(\d+)\.(\d+)\b', 
            lambda match: self._convert_decimal_number(match.group(1), match.group(2)),
            text
        )
        
        # Convert large numbers (process larger numbers first to avoid partial matches)
        text = re.sub(
            r'\b\d{1,100}\b', 
            lambda match: self._convert_number(match.group(0)),
            text
        )
        
        text = re.sub(r'(\d+)([^\d\s])', r'\1 \2', text)
        
        return text
    
    def _separate_alphanumeric(self, text):
        """
        Separate mixed alphanumeric strings by inserting spaces between different character types.
        Example: 22T583XYZ -> 22 T 583 XYZ
        """
        result = []
        current_type = None  # None, 'alpha', or 'digit'
        
        for char in text:
            if char.isalpha():
                new_type = 'alpha'
            elif char.isdigit():
                new_type = 'digit'
            else:
                new_type = None
            
            # If type changed, add space (except for initial character)
            if current_type is not None and new_type != current_type and new_type is not None:
                result.append(' ')
            
            result.append(char)
            current_type = new_type
        
        return ''.join(result)
    
    def _convert_decimal_number(self, integer_part, decimal_part):
        """
        Convert a decimal number to its Vietnamese text representation.
        The integer part is converted normally, while the decimal part is read digit by digit.
        """
        integer_text = self._convert_number(integer_part)
        
        # Convert decimal digits one by one
        decimal_digits = []
        for digit in decimal_part:
            decimal_digits.append(self.numbers_dict[digit])
        
        decimal_text = " ".join(decimal_digits)
        
        return f"{integer_text} phẩy {decimal_text}"
    
    def _convert_number(self, number_str):
        """
        Convert a number to its Vietnamese text representation.
        This is the main entry point for number conversion.
        """
        try:
            # Remove leading zeros
            number_str = number_str.lstrip('0')
            if not number_str:
                return self.numbers_dict['0']
                
            # Handle numbers that would cause int overflow
            if len(number_str) > 18:
                return self._read_number_by_digits(number_str)
                
            num = int(number_str)
            
            # For zero
            if num == 0:
                return self.numbers_dict['0']
                
            # For small numbers
            if num < 1000:
                return self._convert_small_number(num)
                
            # Get the proper Vietnamese representation
            return self._convert_large_number_properly(num)
            
        except (ValueError, KeyError):
            return number_str
            
    def _convert_large_number_properly(self, num):
        """
        Convert a large number (≥1000) using proper Vietnamese number reading rules.
        This method avoids the incorrect zero groups in the middle.
        """
        if num == 0:
            return self.numbers_dict['0']
            
        # Split the number into groups of 3 digits from right to left
        groups = []
        temp = num
        while temp > 0:
            groups.append(temp % 1000)
            temp //= 1000
            
        # Process each group with its corresponding unit
        result = []
        for i in range(len(groups) - 1, -1, -1):
            group = groups[i]
            
            # Skip zero groups, except for the last (rightmost) group
            if group == 0 and i != 0:
                continue
                
            # Convert this group
            if group != 0:  # Only add non-zero groups
                group_text = self._convert_small_number(group)
                
                # Add the unit if not the ones group (rightmost)
                if i > 0 and i < len(self.units):
                    group_text += f" {self.units[i]}"
                    
                result.append(group_text)
                
        return " ".join(result)
    
    def _read_number_by_digits(self, number_str):
        """Read very large numbers digit by digit"""
        result = []
        for digit in number_str:
            result.append(self.numbers_dict[digit])
        return " ".join(result)
    
    def _convert_small_number(self, num):
        """Convert a number less than 1000 to Vietnamese text"""
        if num == 0:
            return self.numbers_dict['0']
            
        if 1 <= num <= 9:
            return self.numbers_dict[str(num)]
            
        if 10 <= num <= 19:
            if num == 10:
                return "mười"
            return f"mười {self._convert_single_digit(num % 10, True)}"
            
        if 20 <= num <= 99:
            tens = num // 10
            ones = num % 10
            if ones == 0:
                return f"{self.numbers_dict[str(tens)]} mươi"
            else:
                return f"{self.numbers_dict[str(tens)]} mươi {self._convert_single_digit(ones, True)}"
                
        if 100 <= num <= 999:
            hundreds = num // 100
            remainder = num % 100
            
            if remainder == 0:
                return f"{self.numbers_dict[str(hundreds)]} trăm"
            elif remainder < 10:
                return f"{self.numbers_dict[str(hundreds)]} trăm lẻ {self.numbers_dict[str(remainder)]}"
            else:
                tens = remainder // 10
                ones = remainder % 10
                
                if tens == 0:
                    return f"{self.numbers_dict[str(hundreds)]} trăm lẻ {self.numbers_dict[str(ones)]}"
                elif tens == 1:
                    if ones == 0:
                        return f"{self.numbers_dict[str(hundreds)]} trăm mười"
                    else:
                        return f"{self.numbers_dict[str(hundreds)]} trăm mười {self._convert_single_digit(ones, True)}"
                else:
                    if ones == 0:
                        return f"{self.numbers_dict[str(hundreds)]} trăm {self.numbers_dict[str(tens)]} mươi"
                    else:
                        return f"{self.numbers_dict[str(hundreds)]} trăm {self.numbers_dict[str(tens)]} mươi {self._convert_single_digit(ones, True)}"
    
    def _convert_single_digit(self, digit, is_tens_place=False):
        """Convert a single digit with special handling for tens place"""
        if is_tens_place:
            if digit == 1:
                return "mốt"
            elif digit == 4:
                return "tư"  # Some dialects prefer "tư" after tens
            elif digit == 5:
                return "lăm"
            else:
                return self.numbers_dict[str(digit)]
        return self.numbers_dict[str(digit)]
    
    def _convert_date(self, day, month, year, day_first=True):
        """
        Convert a date to Vietnamese text representation
        
        Args:
            day: Day component of the date
            month: Month component of the date
            year: Year component of the date
            day_first: Whether the date format has day first (DD/MM/YYYY) or year first (YYYY-MM-DD)
        """
        # Remove leading zeros
        day = day.lstrip('0') or '0'
        month = month.lstrip('0') or '0'
        
        # Convert components to text
        day_text = self._convert_number(day)
        month_text = self.month_names.get(month, self._convert_number(month))
        year_text = self._convert_number(year)
        
        # Format as "ngày [day] tháng [month] năm [year]"
        return f"ngày {day_text} tháng {month_text} năm {year_text}"
    
    def _convert_datetime(self, year, month, day, hour, minute, second):
        """
        Convert a datetime to Vietnamese text representation
        """
        date_part = self._convert_date(day, month, year, day_first=False)
        
        # Convert time components
        hour = hour.lstrip('0') or '0'
        minute = minute.lstrip('0') or '0'
        second = second.lstrip('0') or '0'
        
        hour_text = self._convert_number(hour)
        minute_text = self._convert_number(minute)
        second_text = self._convert_number(second)
        
        time_text = f"giờ {hour_text} phút {minute_text} giây {second_text}"
        
        return f"{date_part} {time_text}"


def normalize_vietnamese_text(text):
    """
    Normalize Vietnamese text for text-to-speech input.
    
    Args:
        text (str): Input text to normalize
    
    Returns:
        str: Normalized text
    """
    normalizer = VietnameseTextNormalizer()
    return normalizer.normalize(text)