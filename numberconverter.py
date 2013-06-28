# numberconverter.py

# These tuples are used when determining how to write out a number.
ones = ("zero", "one", "two", "three", "four", "five",
                "six", "seven", "eight", "nine")
tens = ("", "ten", "twenty", "thirty", "forty", "fifty",
                 "sixty", "seventy", "eighty", "ninety")
other = ("", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
             "sixteen", "seventeen", "eighteen", "nineteen")

# This tuple is used to remove all non-digits from the inputted number.
digits = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
             
def convertNum(n, year = True):

    """Accepts an inputted number as either a string,
    int, long, or float (it will truncate the decimal),
    and returns that number as a "written-out" string,
    e.g. "123" will become "one hundred twenty-three".
    If a number is longer than nine digits, then it will
    return a string with each of the digits written out,
    e.g. "1-800-867-5309" becomes "one eight zero zero
    eight six seven five three zero nine". Also accepts
    an addition parameter indicating whether "year mode"
    should be used, meaning that numbers such as "1814"
    should be written out as "eighteen fourteen" rather
    than "one thousand, eight hundred fourteen." Note
    that the default setting for year mode is True."""

    if type(n) == str:
        s = "".join(c for c in n if c in digits)
        p = len(s)
        if not p: return
        else: n = int(s)
    elif type(n) == int or type(n) == long:
        s = str(n)
        p = len(s)
    elif type(n) == float:
        n = int(n)
        s = str(n)
        p = len(s)
    else:
        return n

    return getNums(p, s, year)


def getNums(p, s, year):

    """Returns the written-out number."""

    m, t, h = "", "", ""

    if year:
        if p == 4:
            if int(s[1:3]):
                if not int(s[2]):
                    z = " o' "
                else:
                    z = " "
                return (onesTensPlaces(s[:2]) +
                        z + onesTensPlaces(s[2:]))
    if p < 4:
        h = getPlaces(s)
    elif p < 7:
        t = getPlaces(s[:p-3]) 
        h = getPlaces(s[p-3:])
    elif p < 10:
        m = getPlaces(s[:p-6])
        t = getPlaces(s[p-6:p-3])
        h = getPlaces(s[p-3:])
    else:
        d = ""
        for c in s:
            d += onesPlace(c) + " "
        return d.strip()
    
    return concatenateNums(m, t, h)


def getPlaces(s):

    """Returns the string representation the
    millions, thousands, or hundreds places."""
    
    if len(s) == 3:
        return onesTensHundredsPlaces(s)
    elif len(s) == 2:
        return onesTensPlaces(s)
    elif len(s) == 1:
        return onesPlace(s)
        
def onesPlace(s):

    """Returns the string representation of one place."""
    
# Returns the ones-place number.
    return ones[int(s)]


def onesTensPlaces(s):

    """Returns the string representation of two places."""
    
    if not int(s[0]):
        return onesPlace(s[1])
# Checks if the number is in the "other" tuple
# (the numbers eleven through nineteen) or the
# "tens" tuple. Stores whichever into r.
    if int(s) > 10 and int(s) < 20:
        r = other[int(s[1])]
    else:
        r = tens[int(s[0])]
    # Checks to see if the ones place is not zero.
    # If true, then the ones place is concatenated with a hyphen.
        if int(s[1]) != 0:
            r += "-" + ones[int(s[1])]
# Returns the result.            
    return r

    
def onesTensHundredsPlaces(s):

    """Returns the string representation of three places"""
    
    if not int(s[0]):
        return onesTensPlaces(s[1:])
# Determines the hundreds place and stores it into r.
    r = ones[int(s[0])] + " hundred"
# Checks if the remaining two digits are in the "other" tuple
# (the numbers starting with eleven and ending with nineteen).
# Concatenates it to r if the two digits are in this list.
    if int(s[1:3]) > 10 and int(s[1:3]) < 20:
        r += " " + other[int(s[2])]
# Checks to see if the remaining two digits are not "00".
# Concatenates the tens place to r if they are not "00".
    elif int(s[1:3]) != 0:
        r += " " + tens[int(s[1])]
    # Checks to see if the tens place is not zero.
    # If true, checks to see if the ones place is not zero
    # and concatenates the ones place with a hyphen if true.
    # Else, (if the tens place is zero), then the ones
    # place is concatenated without a hyphen.
        if int(s[1]):
            if int(s[2]):
                r += "-" + ones[int(s[2])]
        else:
            r += ones[int(s[2])]
# Returns the result.            
    return r


def concatenateNums(m, t, h):
    
    """Performs various if/elif/else checks
    to concatenate the number strings properly,
    and returns the concatenated string."""
    
    if m == "zero": m = ""
    elif m: m += " million"

    if t == "zero": t = ""
    elif t: t += " thousand"

    if not t and m:
        if "hundred" in h:
            m += ", "
        else: m += " "
    elif m: m += ", "

    if h == "zero":
        if m or t: h = ""
    elif "hundred" in h:
        if t: t += ", "
    elif t: t += " "

    return m + t + h


def main():

    """Main method of numberconverter.py"""
    
    print("Welcome to the number converter.")
    print("Enter a blank line at any time to quit.")
    done = False
    while not done:
        try: number = raw_input(">>> ")
        except: number = input(">>> ")
        if not number: done = True
        else: print(convertNum(number))
    print("Zaijian!")


if __name__ == "__main__":
    main()
