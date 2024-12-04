formattest = """
{{
  ""hello"":
}}
{arg1}
hello
{arg2}
}}
"""

test1 = formattest.format(arg1="hi", arg2="bye")

print(test1)