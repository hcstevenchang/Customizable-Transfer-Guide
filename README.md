# Customizable_Transfer_Guide

This is a Transfer Guide (乗換案内) for Japan with a customizable transfer time

## Description

* Extracted train time table data from the train schedule website (Yahoo!路線情報).
* Created an algorithm for transfer guide with  customizable transfer time.

## Result

```python
import datetime
def main():
    timestamp=datetime.datetime.strptime('2022-06-17 10:00','%Y-%m-%d %H:%M')
    for line in writetimeline(fastertime('高円寺','池袋',timestamp,0)):
        print(line)

if __name__ == "__main__":
    main()

#### Output
```text
Route.1️⃣9:44→09:59 (15分) trf:1 220
09:44発 高円寺 4 前/中/後
⬇️6分 🀄JR中央線・東京行
09:50着 新宿 8
🚶‍♀️ 4分 乗り換え
09:54発 新宿 4
⬇️5分 🟧JR湘南新宿ライン・古河行
09:59着 池袋 3

Route.2️⃣9:39→09:56 (17分) trf:1 420
09:39発 高円寺 2 中/後
⬇️8分 Ⓜ️Metro東西線・東葉勝田台行
09:47着 高田馬場 1
🚶‍♀️ 5分 乗り換え
09:52発 高田馬場 1
⬇️4分 🟩JR山手線外・池袋上野方面
09:56着 池袋 7