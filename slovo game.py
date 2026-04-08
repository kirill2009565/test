import random

spisok1 = ["Кос","Сам","Длин","Быстр"]
spisok2 = ["глазый","лёт","рукий","ногий"]
scenxbr = [0,0]
while True:
    slo1 = random.choice(spisok1)
    slo2 = random.choice(spisok2)
    slovo = slo1 + "о" + slo2
    print(f"Я объяденил корни слов {slo1} и {slo2} \n напиши это слово правильно")
    pler = input()
    if pler == slovo:
        scenxbr[0] += 1
        print("Молодец все правильно")
        print(f"человек: {scenxbr[0]} его невежество: {scenxbr[1]}")
    else:
        scenxbr[1] += 1
        print("ошибка попробуй ещё раз")
        print(f"человек: {scenxbr[0]} его невежество: {scenxbr[1]}")
