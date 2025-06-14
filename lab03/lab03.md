# Практика 3. Прикладной уровень

## Программирование сокетов. Веб-сервер

### А. Однопоточный веб-сервер (3 балла)
Вам необходимо разработать простой веб-сервер, который будет возвращать содержимое
локальных файлов по их имени. В этом задании сервер умеет обрабатывать только один запрос и
работает в однопоточном режиме. Язык программирования вы можете выбрать любой.
Требования:
- веб-сервер создает сокет соединения при контакте с клиентом (браузером) получает HTTP-запрос из этого соединения
- анализирует запрос, чтобы определить конкретный запрашиваемый файл
- находит запрошенный файл в своей локальной файловой системе
- создает ответное HTTP-сообщение, состоящее из содержимого запрошенного файла и предшествующих ему строк заголовков
- отправляет ответ через TCP-соединение обратно клиенту
- если браузер запрашивает файл, которого нет на веб-сервере, то сервер должен вернуть сообщение об ошибке «404 Not Found»

Ваша задача – разработать и запустить свой локальный веб-сервер, а затем проверить его
работу при помощи отправки запросов через браузер. Продемонстрируйте работу сервера, приложив скрины.

Скорее всего порт 80 у вас уже занят, поэтому вам необходимо использовать другой порт для
работы вашей программы.

Формат команды для запуска сервера:
```
<server.exe> server_port
```

#### Демонстрация работы
существующий 
<img src="A_exist.png" width=500 />
несуществующий
<img src="A_unknown.png.png" width=500 />

### Б. Многопоточный веб-сервер (2 балла)
Реализуйте многопоточный сервер, который мог бы обслуживать несколько запросов
одновременно. Сначала создайте основной поток (процесс), в котором ваш модифицированный
сервер ожидает клиентов на определенном фиксированном порту. При получении запроса на
TCP-соединение от клиента он будет устанавливать это соединение через другой порт и
обслуживать запрос клиента в отдельном потоке. Таким образом, для каждой пары запрос-ответ
будет создаваться отдельное TCP-соединение в отдельном потоке.
#### Демонстрация работы
<img src="B1.png" width=500 />
<img src="B2.png" width=500 />

### В. Клиент (2 балла)
Вместо использования браузера напишите собственный HTTP-клиент для тестирования вашего
веб-сервера. Ваш клиент будет поддерживать работу с командной строкой, подключаться к
серверу с помощью TCP-соединения, отправлять ему HTTP-запрос с помощью метода GET и
отображать ответ сервера в качестве результата. Клиент должен будет в качестве входных
параметров принимать аргументы командной строки, определяющие IP-адрес или имя сервера,
порт сервера и имя файла на сервере. Продемонстрируйте работу клиента, приложив скрины. 

Формат команды для запуска клиента:
```
<client.exe> server_host server_port filename
```

#### Демонстрация работы
<img src="C1.png" width=500 />

<img src="C2.png" width=500 />

<img src="C3.png" width=500 />

### Г. Ограничение потоков сервера (3 балла)
Пусть ресурсы вашего сервера ограничены и вы хотите контролировать максимальное количество
потоков, с которыми может работать ваш многопоточный сервер одновременно. При запуске
сервер получает целочисленное значение `concurrency_level` из командной строки. Если сервер 
получает запрос от клиента, и при этом уже запущено максимальное количество потоков, то 
запрос от клиента блокируется (встает в очередь) и дожидается, пока не закончит работу 
один из запущенных потоков. После этого сервер может запустить новый поток для обработки 
запроса от клиента.

Формат команды для запуска сервера:
```
<server.exe> server_port concurrency_level
```
#### Демонстрация работы
<img src="D1.png" width=500 />

<img src="D2.png" width=500 />
## Задачи

### Задача 1 (2 балла)
Голосовые сообщения отправляются от хоста А к хосту Б в сети с коммутацией пакетов в режиме
реального времени. Хост А преобразует на лету аналоговый голосовой сигнал в цифровой поток
битов, имеющий скорость $128$ Кбит/с, и разбивает его на $56$-байтные пакеты. Хосты А и Б
соединены одной линией связи, в которой скорость передачи данных равна $1$ Мбит/с, а задержка
распространения составляет $5$ мс. Как только хост А собирает пакет, он посылает его на хост Б,
который, в свою очередь, при получении всего пакета преобразует биты в аналоговый сигнал.
Сколько времени проходит с момента создания бита (из исходного аналогового сигнала на хосте
A) до момента его декодирования (превращения в часть аналогового сигнала на хосте Б)?

#### Решение
1. **Размер пакета в битах.**  
   $
     56\;\text{байт} = 56 \times 8 = 448\;\text{бит}.
   $

2. **Время формирования полного пакета на A.**  
   Поток генерируется со скоростью $128\;\text{Кбит/с} = 128\,000\;\text{бит/с}.$  
   Чтобы накопить 448 бит, требуется  
   $
     t_{\text{сбор}} = \frac{448\;\text{бит}}{128\,000\;\text{бит/с}}
       = 0{,}0035\;\text{с} = 3{,}5\;\text{мс}.
   $
   (До тех пор первые биты пакета ждут, пока весь пакет не сформируется.)

3. **Время передачи пакета по линии.**  
   Скорость линии \(R = 1\,000\,000\;\text{бит/с} = 1\;\text{Мбит/с}.\)  
   На сериализацию 448 бит тратится  
   $
     t_{\text{перед}} = \frac{448\;\text{бит}}{1\,000\,000\;\text{бит/с}}
       = 0{,}000448\;\text{с} = 0{,}448\;\text{мс}.
   $

4. **Задержка распространения (однократно).**  
   $\displaystyle t_{\text{проп}} = 5\;\text{мс}.$

5. **Итого: задержка «от создания первого бита в пакете до декодирования этого бита»**  
   - «Первый бит» пакета появляется в потоке в момент \(t=0\).  
   - Но он не может быть передан, пока весь пакет (все 448 бит) не сформируется: первые биты ждут до \(t = t_{\text{сбор}} = 3{,}5\;\text{мс}.\)  
   - В момент \(t = 3{,}5\;\text{мс}\) хост A начинает сериализацию всего пакета. Последний (448-й) бит покидает передатчик A в момент  
     $
       t = 3{,}5\;\text{мс} + 0{,}448\;\text{мс} = 3{,}948\;\text{мс}.
     $
   - Этот последний бит затем распространяется по линии \(5\;\text{мс}\), так что последним бит пакета «приземляется» на B в момент  
     $
       t = 3{,}948\;\text{мс} + 5{,}0\;\text{мс} = 8{,}948\;\text{мс}.
     $
   - Согласно условию, хост B сможет «декодировать» биты в аналоговый сигнал только после получения **всего** пакета, то есть после прихода последнего (448-го) бита.

Поэтому **время от создания (На A) первого (начального) бита выбранного пакета до его окончательного декодирования (На B)** равно
$
  \boxed{8{,}948\;\text{мс}.}
$



### Задача 2 (2 балла)
Рассмотрим буфер маршрутизатора, где пакеты хранятся перед передачей их в исходящую линию
связи. В этой задаче вы будете использовать широко известную из теории массового
обслуживания (или теории очередей) формулу Литтла. Пусть $N$ равно среднему числу пакетов в
буфере плюс пакет, который передается в данный момент. Обозначим через $a$ скорость
поступления пакетов в буфер, а через $d$ – среднюю общую задержку (т.е. сумму задержек
ожидания и передачи), испытываемую пакетом. Согласно формуле Литтла $N = a \cdot d$.
Предположим, что в буфере содержится в среднем $10$ пакетов, а средняя задержка ожидания для
пакета равна $10$ мс. Скорость передачи по линии связи составляет $100$ пакетов в секунду.
Используя формулу Литтла, определите среднюю скорость поступления пакета в очередь,
предполагая, что потери пакетов отсутствуют.

#### Решение

1.  
**Среднее число пакетов в системе**  
(в буфере + в передаче) равно  
$
  N = 10 \;(\text{в буфере}) \;+\; 1 \;(\text{пакет в передаче}) \;=\; 11.
$

2.  
**Задержка передачи одного пакета** при скорости $\displaystyle 100$ пакетов/с:
$
  d_{\text{перед}} = \frac{1}{100}\;\text{с} = 0{,}01\;\text{с} = 10\;\text{мс}.
$

3.  
**Задержка ожидания** (waiting time) дана как $10$ мс $= 0{,}01$ с.  
Следовательно, **общая задержка** \(d\) (ожидание + передача) равна  
$
  d = d_{\text{ожид}} + d_{\text{перед}}
    = 0{,}01\;\text{с} + 0{,}01\;\text{с}
    = 0{,}02\;\text{с} = 20\;\text{мс}.
$

4.  
По формуле Литтла $N = a \cdot d$ имеем  
$
  11 = a \cdot 0{,}02,
  \quad
  \Longrightarrow
  \quad
  a = \frac{11}{0{,}02} = 550\;\text{пакетов/с}.
$

**Ответ:**  
$
  a = 550\;\text{пакетов в секунду}.
$

### Задача 3 (2 балла)
Рассмотрим рисунок.

<img src="images/task3.png" width=500 />

Предположим, нам известно, что на маршруте от сервера до клиента узким местом
является первая линия связи, скорость передачи данных по которой равна $R_S$ бит/с.
Допустим, что мы отправляем два пакета друг за другом от сервера клиенту, и другой
трафик на маршруте отсутствует. Размер каждого пакета составляет $L$ бит, а скорость
распространения сигнала по обеим линиям равна $d_{\text{распространения}}$.
1. Какова временная разница прибытия пакетов к месту назначения? То есть, сколько
времени пройдет от момента получения клиентом последнего бита первого пакета до
момента получения последнего бита второго пакета?
2. Теперь предположим, что узким местом является вторая линия связи (то есть $R_C < R_S$).
Может ли второй пакет находиться во входном буфере, ожидая передачи во вторую
линию? Почему? Если предположить, что сервер отправляет второй пакет, спустя $T$ секунд
после отправки первого, то каково должно быть минимальное значение $T$, чтобы очередь
во вторую линию связи была нулевая? Обоснуйте ответ.

#### Решение
todo

### Задача 4 (4 балла)

<img src="images/task4.png" width=400 />

На рисунке показана сеть организации, подключенная к Интернету:
Предположим, что средний размер объекта равен $850000$ бит, а средняя скорость
запросов от браузеров этой организации к веб-серверам составляет $16$ запросов в секунду.
Предположим также, что количество времени, прошедшее с момента, когда внешний
маршрутизатор организации пересылает запрос HTTP, до момента, пока он не получит
ответ, равно в среднем три секунды. Будем считать, что общее среднее время ответа
равно сумме средней задержки доступа (то есть, задержки от маршрутизатора в
Интернете до маршрутизатора организации) и средней задержки в Интернете. Для
средней задержки доступа используем формулу $\dfrac{\Delta}{1 - \Delta \cdot B}$, 
где $\Delta$ – это среднее время, необходимое для отправки объекта по каналу связи, 
а B – частота поступления объектов в линию связи.
1. Найдите $\Delta$ (это среднее время, необходимое для отправки объекта по каналу связи).
2. Найдите общее среднее время ответа.
3. Предположим, что в локальной сети организации присутствует кэширующий
сервер. Пусть коэффициент непопадания в кэш равен $0.4$. Найдите общее время ответа.

#### Решение
todo
