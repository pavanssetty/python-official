import pyperclip
dateList = pyperclip.paste().split()

convertedDateList = []
for each in dateList:
    convDate = each[6:]+'/'+each[4:6]+'/'+each[0:4]
#    print(convDate)
    convertedDateList.append(convDate)
pyperclip.copy("\n".join(convertedDateList))
print(str(convertedDateList))
