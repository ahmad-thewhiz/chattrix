from __future__ import annotations

import re
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# Message data class
@dataclass
class Message:
    sender: str
    text: str
    date: datetime


# Regex patterns
DATE_LINE_REGEX = re.compile(
    r"^(\d{1,2})/(\d{1,2})/(\d{2,4}),\s+(.+?)\s-\s([^:]+):\s(.*)$"
)
SYSTEM_LINE_REGEX = re.compile(
    r"^(\d{1,2})/(\d{1,2})/(\d{2,4}),\s+(.+?)\s-\s(.*)$"
)

DELETED_PATTERNS = (
    "This message was deleted",
    "You deleted this message",
)

EDITED_PATTERNS = (
    "<This message was edited>",
)


def _parse_year(two_or_four_digit_year: str) -> int:
    """
        Parse a two or four digit year string into an integer.
    """
    if len(two_or_four_digit_year) == 2:
        return 2000 + int(two_or_four_digit_year)
    return int(two_or_four_digit_year)


def is_omitted(text: str) -> bool:
    """
        Check if the message is omitted.
    """
    return "<Media omitted>" in text


def is_deleted(text: str) -> bool:
    """
        Check if the message is deleted.
    """
    for p in DELETED_PATTERNS:
        if p in text:
            return True
    return False


def strip_edited_markers(text: str) -> str:
    """
        Remove editing markers from the message text.
    """
    result = text
    for p in EDITED_PATTERNS:
        result = result.replace(p, "").strip()
    return result


def compute_stats(messages: List[Message]) -> Dict:
    """
        Compute statistics from the list of messages.
    """
    
    filtered: List[Message] = []
    media_omitted_count: List[Message] = []
    
    for msg in messages:
        if is_omitted(msg.text):
            media_omitted_count.append(msg)
            continue

        if is_deleted(msg.text):
            continue
        
        cleaned_text = strip_edited_markers(msg.text)
        filtered.append(Message(sender=msg.sender, text=cleaned_text, date=msg.date))

    # Identify top two senders
    sender_counts = Counter(m.sender for m in filtered)
    top_two = [s for s, _ in sender_counts.most_common(2)]
    
    if len(top_two) < 2:
        # If only one sender found, fabricate second as Unknown for structure
        while len(top_two) < 2:
            top_two.append("Unknown")

    person1_name, person2_name = top_two[0], top_two[1]

    # Aggregate stats
    stats: Dict[str, Dict[str, float]] = {
        person1_name: {"messages": 0, "characters": 0},
        person2_name: {"messages": 0, "characters": 0},
    }

    # Monthly counts per year
    years = [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]
    monthly: Dict[int, Dict[int, Dict[str, int]]] = {
        y: {m: {person1_name: 0, person2_name: 0} for m in range(1, 13)} for y in years
    }

    # Sorry word tracking
    sorry_patterns = ['sry', 'sorry', 'sory', 'Sorry', 'SORRY', 'SRY']
    sorry_counts: Dict[str, int] = {person1_name: 0, person2_name: 0}
    
    # Media and link tracking
    media_counts: Dict[str, int] = {person1_name: 0, person2_name: 0}
    link_counts: Dict[str, int] = {person1_name: 0, person2_name: 0}
    
    # Emoji tracking
    emoji_counts: Dict[str, int] = {person1_name: 0, person2_name: 0}
    
    # Active days tracking
    active_days: Dict[str, set] = {person1_name: set(), person2_name: set()}
    current_year = datetime.now().year

    for msg in media_omitted_count:
        media_counts[msg.sender] += 1

    for msg in filtered:
        if msg.sender not in stats:
            continue
        
        if is_omitted(msg.text) or is_deleted(msg.text):
            continue

        stats[msg.sender]["messages"] += 1
        stats[msg.sender]["characters"] += len(msg.text.strip())

        # Monthly message counts
        y = msg.date.year
        if y in monthly:
            monthly[y][msg.date.month][msg.sender] += 1

        # Track active days in current year
        if y == current_year:
            active_days[msg.sender].add(msg.date.date())

        # Count sorry words in message
        msg_text_lower = msg.text.lower()
        for pattern in sorry_patterns:
            if pattern.lower() in msg_text_lower:
                sorry_counts[msg.sender] += 1
                break  # Count only once per message even if multiple sorry words

        # Count links (URLs)
        import re
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        if re.search(url_pattern, msg.text):
            link_counts[msg.sender] += 1

        # Count emojis using comprehensive Unicode ranges and modern emoji detection
        emoji_count = 0
        for char in msg.text:
            # Check for comprehensive emoji Unicode ranges
            char_code = ord(char)
            if (0x1F600 <= char_code <= 0x1F64F or  # Emoticons
                0x1F300 <= char_code <= 0x1F5FF or  # Miscellaneous Symbols and Pictographs
                0x1F680 <= char_code <= 0x1F6FF or  # Transport and Map Symbols
                0x1F1E0 <= char_code <= 0x1F1FF or  # Regional Indicator Symbols
                0x2600 <= char_code <= 0x26FF or    # Miscellaneous Symbols
                0x2700 <= char_code <= 0x27BF or    # Dingbats
                0x1F900 <= char_code <= 0x1F9FF or  # Supplemental Symbols and Pictographs
                0x1FA70 <= char_code <= 0x1FAFF or  # Symbols and Pictographs Extended-A
                0x1FAB0 <= char_code <= 0x1FABF or  # Symbols and Pictographs Extended-B
                0x1FAC0 <= char_code <= 0x1FAFF or  # Symbols and Pictographs Extended-C
                0x1FAD0 <= char_code <= 0x1FAFF or  # Symbols and Pictographs Extended-D
                0x1FAE0 <= char_code <= 0x1FAFF or  # Symbols and Pictographs Extended-E
                0x1FAF0 <= char_code <= 0x1FAFF or  # Symbols and Pictographs Extended-F
                0x1F000 <= char_code <= 0x1F02F or  # Mahjong Tiles
                0x1F030 <= char_code <= 0x1F09F or  # Domino Tiles
                0x1F0A0 <= char_code <= 0x1F0FF or  # Playing Cards
                0x1F100 <= char_code <= 0x1F1FF or  # Enclosed Alphanumeric Supplement
                0x1F200 <= char_code <= 0x1F2FF or  # Enclosed Ideographic Supplement
                0x1F300 <= char_code <= 0x1F3FF or  # Miscellaneous Symbols and Pictographs
                0x1F400 <= char_code <= 0x1F4FF or  # Miscellaneous Symbols and Pictographs
                0x1F500 <= char_code <= 0x1F5FF or  # Miscellaneous Symbols and Pictographs
                0x1F600 <= char_code <= 0x1F64F or  # Emoticons
                0x1F650 <= char_code <= 0x1F67F or  # Ornamental Dingbats
                0x1F680 <= char_code <= 0x1F6FF or  # Transport and Map Symbols
                0x1F700 <= char_code <= 0x1F77F or  # Alchemical Symbols
                0x1F780 <= char_code <= 0x1F7FF or  # Geometric Shapes Extended
                0x1F800 <= char_code <= 0x1F8FF or  # Supplemental Arrows-C
                0x1F900 <= char_code <= 0x1F9FF or  # Supplemental Symbols and Pictographs
                0x1FA00 <= char_code <= 0x1FA6F or  # Chess Symbols
                0x1FA70 <= char_code <= 0x1FAFF or  # Symbols and Pictographs Extended-A
                0x1FB00 <= char_code <= 0x1FBFF or  # Symbols for Legacy Computing
                0x1FC00 <= char_code <= 0x1FCFF or  # Symbols for Legacy Computing
                0x1FD00 <= char_code <= 0x1FDFF or  # Symbols for Legacy Computing
                0x1FE00 <= char_code <= 0x1FEFF or  # Symbols for Legacy Computing
                0x1FF00 <= char_code <= 0x1FFFF or  # Symbols for Legacy Computing
                0x20000 <= char_code <= 0x2A6DF or  # CJK Unified Ideographs Extension B
                0x2A700 <= char_code <= 0x2B73F or  # CJK Unified Ideographs Extension C
                0x2B740 <= char_code <= 0x2B81F or  # CJK Unified Ideographs Extension D
                0x2B820 <= char_code <= 0x2CEAF or  # CJK Unified Ideographs Extension E
                0x2CEB0 <= char_code <= 0x2EBEF or  # CJK Unified Ideographs Extension F
                0x2F800 <= char_code <= 0x2FA1F or  # CJK Compatibility Ideographs Supplement
                0xE0000 <= char_code <= 0xE007F or  # Tags
                0xE0100 <= char_code <= 0xE01EF or  # Variation Selectors Supplement
                0xFE000 <= char_code <= 0xFE0FF or  # Variation Selectors
                0xFE100 <= char_code <= 0xFE1FF or  # Variation Selectors
                0xFE200 <= char_code <= 0xFE2FF or  # Variation Selectors
                0xFE300 <= char_code <= 0xFE3FF or  # Variation Selectors
                0xFE400 <= char_code <= 0xFE4FF or  # Variation Selectors
                0xFE500 <= char_code <= 0xFE5FF or  # Variation Selectors
                0xFE600 <= char_code <= 0xFE6FF or  # Variation Selectors
                0xFE700 <= char_code <= 0xFE7FF or  # Variation Selectors
                0xFE800 <= char_code <= 0xFE8FF or  # Variation Selectors
                0xFE900 <= char_code <= 0xFE9FF or  # Variation Selectors
                0xFEA00 <= char_code <= 0xFEAFF or  # Variation Selectors
                0xFEB00 <= char_code <= 0xFEBFF or  # Variation Selectors
                0xFEC00 <= char_code <= 0xFECFF or  # Variation Selectors
                0xFED00 <= char_code <= 0xFEDFF or  # Variation Selectors
                0xFEE00 <= char_code <= 0xFEEFF or  # Variation Selectors
                0xFEF00 <= char_code <= 0xFEFFF or  # Variation Selectors
                0xFF000 <= char_code <= 0xFFFFF or  # Private Use Area
                0x100000 <= char_code <= 0x10FFFF):  # Supplementary Private Use Area-B
                emoji_count += 1
        
        # Also check for combining characters and zero-width joiners that form emoji sequences
        if any(ord(c) in [0x200D, 0xFE0F, 0x1F3FB, 0x1F3FC, 0x1F3FD, 0x1F3FE, 0x1F3FF] for c in msg.text):
            emoji_count += 1
            
        emoji_counts[msg.sender] += emoji_count


    def calc_avg(sender_name: str) -> float:
        """
            Calculate the average message length for a given sender.
        """
        messages_count = stats[sender_name]["messages"]
        if messages_count == 0:
            return 0.0
        return round(stats[sender_name]["characters"] / messages_count, 2)


    def calc_sorry_count(sender_name: str) -> int:
        """
            Calculate the count of 'sorry' messages for a given sender.
        """
        return sorry_counts[sender_name]

   
    def calc_media_count(sender_name: str) -> int:
        """
            Calculate the count of media messages for a given sender.
        """
        return media_counts[sender_name]


    def calc_link_count(sender_name: str) -> int:
        """
            Calculate the count of link messages for a given sender.
        """
        return link_counts[sender_name]


    def calc_emoji_count(sender_name: str) -> int:
        """
            Calculate the count of emoji messages for a given sender.
        """
        return emoji_counts[sender_name]


    def calc_active_days_percentage(sender_name: str) -> float:
        """
            Calculate the percentage of active days for a given sender.
        """
        active_count = len(active_days[sender_name])
        # Calculate days elapsed in current year
        start_of_year = datetime(current_year, 1, 1)
        end_of_year = datetime(current_year, 12, 31)
        days_elapsed = min((datetime.now() - start_of_year).days + 1, 366)  # Account for leap year
        if days_elapsed == 0:
            return 0.0
        return round((active_count / days_elapsed) * 100, 1)

    def calc_monthly_growth(sender_name: str) -> float:
        """
            Calculate the monthly growth rate for a given sender.
        """
        current_year_data = monthly.get(current_year, {})
        if not current_year_data:
            return 0.0
        
        # Get monthly message counts for current year
        monthly_counts = [current_year_data[m][sender_name] for m in range(1, 13)]
        
        # Calculate month-to-month differences
        month_differences = []
        for i in range(1, len(monthly_counts)):
            if monthly_counts[i-1] > 0:  # Avoid division by zero
                diff = ((monthly_counts[i] - monthly_counts[i-1]) / monthly_counts[i-1]) * 100
                month_differences.append(diff)
        
        if not month_differences:
            return 0.0
        
        # Return average of month-to-month growth rates
        return round(sum(month_differences) / len(month_differences), 1)

    result = {
        "person1": {
            "name": person1_name,
            "messages": stats[person1_name]["messages"],
            "characters": stats[person1_name]["characters"],
            "average_length": calc_avg(person1_name),
            "sorry_count": calc_sorry_count(person1_name),
            "media_count": calc_media_count(person1_name),
            "link_count": calc_link_count(person1_name),
            "emoji_count": calc_emoji_count(person1_name),
            "active_days_percentage": calc_active_days_percentage(person1_name),
            "monthly_growth": calc_monthly_growth(person1_name),
        },
        "person2": {
            "name": person2_name,
            "messages": stats[person2_name]["messages"],
            "characters": stats[person2_name]["characters"],
            "average_length": calc_avg(person2_name),
            "sorry_count": calc_sorry_count(person2_name),
            "media_count": calc_media_count(person2_name),
            "link_count": calc_link_count(person2_name),
            "emoji_count": calc_emoji_count(person2_name),
            "active_days_percentage": calc_active_days_percentage(person2_name),
            "monthly_growth": calc_monthly_growth(person2_name),
        },
        "monthly": monthly,
    }
    
    media_breakdown = {person1_name: {}, person2_name: {}}
    
    for msg in filtered:
        if msg.sender in [person1_name, person2_name]:
            # Only count messages with exact "<Media omitted>" text
            if "<Media omitted>" in msg.text:
                media_type = "Media omitted"
                if media_type not in media_breakdown[msg.sender]:
                    media_breakdown[msg.sender][media_type] = 0
                media_breakdown[msg.sender][media_type] += 1
    
    media_examples = []
    for msg in filtered:
        if "<Media omitted>" in msg.text:
            media_examples.append(f"{msg.sender}: '{msg.text[:100]}...'")
            if len(media_examples) >= 5:  # Show first 5 examples
                break
    
    return result


def parse_whatsapp_export(text: str) -> List[Message]:
    """
        Parse the exported WhatsApp chat text into a list of Message objects.
    """
    messages: List[Message] = []
    current_sender: Optional[str] = None
    current_text_parts: List[str] = []
    current_date: Optional[datetime] = None

    def flush_current() -> None:
        """
            Finalize the current message and add it to the list.
        """
        nonlocal current_sender, current_text_parts, current_date
        if current_sender is not None and current_date is not None:
            combined_text = "\n".join(current_text_parts).strip()
            messages.append(Message(sender=current_sender.strip(), text=combined_text, date=current_date))
        current_sender = None
        current_text_parts = []
        current_date = None

    for raw_line in text.splitlines():
        # Normalize special spaces WhatsApp sometimes uses
        normalized = (
            raw_line.replace("\u202f", " ")  # narrow no-break space
            .replace("\u00a0", " ")  # non-breaking space
            .strip("\ufeff\n\r")
        )

        m = DATE_LINE_REGEX.match(normalized)
        if m:
            # New message starts
            flush_current()
            day, month, year_str, _time, sender, msg_text = m.groups()
            year = _parse_year(year_str)
            try:
                msg_date = datetime(year=year, month=int(month), day=int(day))
            except ValueError:
                # Skip invalid dates
                continue
            current_sender = sender
            current_date = msg_date
            current_text_parts = [msg_text]
        else:
            # System line (date present but no sender colon) -> skip
            sys_match = SYSTEM_LINE_REGEX.match(normalized)
            if sys_match and ":" not in normalized.split(" - ", 1)[-1]:
                flush_current()
                continue

            # Continuation of previous message
            if current_sender is not None:
                current_text_parts.append(raw_line)
            else:
                # Line that doesn't belong to any message; skip
                continue

    # Flush last message
    flush_current()
    return messages