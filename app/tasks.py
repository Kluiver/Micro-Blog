import time


def exemplo(segundos):
    print('Começando tarefa')
    for i in range(segundos):
        print(i)
        time.sleep(1)
    print('Tarefa concluída')