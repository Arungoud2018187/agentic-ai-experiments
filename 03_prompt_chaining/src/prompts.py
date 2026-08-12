STEP_1_PROMPT = """
Extract the important information from the following text.

Return:
- Topic
- Main points
- Important facts
- Key entities
- Important numbers

TEXT:
{text}
"""


STEP_2_PROMPT = """
Analyze the extracted information below.

Identify:
- Main problem
- Causes
- Effects
- Important observations
- Recommended actions

EXTRACTED INFORMATION:
{information}
"""


STEP_3_PROMPT = """
Create a concise summary using the analysis below.

The summary should:
- Be clear
- Be factual
- Avoid unnecessary details
- Preserve important information

ANALYSIS:
{analysis}
"""


STEP_4_PROMPT = """
Create the final structured report.

Use exactly this format:

TITLE:
<appropriate title>

SUMMARY:
<short summary>

KEY FINDINGS:
- finding 1
- finding 2
- finding 3

RECOMMENDATIONS:
- recommendation 1
- recommendation 2
- recommendation 3

SOURCE INFORMATION:
<important facts from the original input>

SUMMARY:
{summary}

ANALYSIS:
{analysis}
"""