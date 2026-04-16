import random
points = {"coap":0,"player":0}

while True:
    a = random.randint(10,90)
    b = random.randint(10,90)
    op = random.choice(("+","-"))
    if op == "+":
        ans = a + b
        user = input(f"{a} + {b} = ")
    else:
        ans = a - b
        user = input(f"{a} - {b} = ")
    if user == str(ans):
        print("верно")
        points["player"] += 1
    else:
        print("ты ошибся ")
        points["coap"] += 1
    print(f"Счёт: {points['player']} : {points['coap']} ")