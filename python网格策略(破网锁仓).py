# fmz@7a22c3f7557c7f0a4aa73d0425181e3d

'''backtest
start: 2019-11-30 00:00:00
end: 2020-01-03 00:00:00
period: 1m
exchanges: [{"eid":"Futures_OKCoin","currency":"BTC_USD"}]
'''
#频繁破网会导致大幅回撤
import json
import talib

# 全局变量
arrNet = []
arrMsg = []
orderbreakgrid = []
breakgriddate = []
breakgridinf = {'numkdc':0,'numxgx':0,'numsgx':0,'numbgx':0,}
acc = None
upgrid = False
lend = 0
newbard = False
xiumianstart = 0
xiumian = False
xiumianrestart = False
jiacang = True
def getposition() :
    chicang=0   #空仓
    if not IsVirtual():
        position = _C(exchange.GetPosition)
        if position :
            if position[0]["Type"] == 0 :
                chicang=1
            else:
                chicang=2
    else:
        position = _C(exchange.GetPosition)
        if position :
            if position[0]["Type"] == 0 :
                chicang=1
            else:
                chicang=2
            #Log(position[0]["Type"],position)
    return {"chicang":chicang,"position":position}

def exbuy (conprice,connum,accfh):
    exchange.SetDirection("buy")
    ordida = exchange.Buy(conprice, connum)
    if not IsVirtual():
        Sleep(110)
    #通过判断订单号以及下单后账户余额是否变化，来判断下单是否成功

    accblan = _C(exchange.GetAccount).Stocks

    while (not ordida) and ((accblan == accfh.Stocks)) :
        if (not IsVirtual()) :
            Sleep(110)
        ordida = exchange.Buy(conprice, connum)
        accblan = _C(exchange.GetAccount).Stocks
    if (not IsVirtual()) :
        Sleep(110)
    ext.PlotFlag(time.time(), "开多", "开多", "flag", "red")
    Log("价格",conprice,"开多",connum,"张，订单已下@")
    return ordida

def exclosesell(conprice,connum,posfh):
    exchange.SetDirection("closesell")
    ordida = exchange.Buy(conprice, connum)
    if not IsVirtual():
        Sleep(110)
    poskp = getposition()
    if not (posfh["chicang"] ==0) and poskp["position"]:
        while (not ordida) and ((posfh["position"][0]["Amount"]==poskp["position"][0]["Amount"]) and poskp["position"][0]["FrozenAmount"]==0) :
            if (not IsVirtual()) :
                Sleep(110)
            ordida = exchange.Buy(conprice, connum)
            poskp = getposition()
            if not (posfh["chicang"] ==0) :
                break
    if not IsVirtual():
        Sleep(110)
    ext.PlotFlag(time.time(), "平空", "平空", "flag", "red")
    Log("价格",conprice,"平空",connum,"张，订单已下@")
    return ordida

def exsell (conprice,connum,accfh) :
    exchange.SetDirection("sell")
    ordida = exchange.Sell(conprice, connum)
    if not IsVirtual():
        Sleep(110)
    #通过判断订单号以及下单后账户余额是否变化，来判断下单是否成功

    accblan = _C(exchange.GetAccount).Stocks

    while (not ordida) and ((accblan == accfh.Stocks)) :
        if (not IsVirtual()) :
            Sleep(110)
        ordida = exchange.Sell(conprice, connum)
        accblan = _C(exchange.GetAccount).Stocks
    if not IsVirtual():
        Sleep(110)
    ext.PlotFlag(time.time(), "开空", "开空", "flag", "green")
    Log("价格",conprice,"开空",connum,"张，订单已下@")
    return ordida

def exclosebuy (conprice,connum,posfh) :
    exchange.SetDirection("closebuy")
    ordida = exchange.Sell(conprice, connum)
    if not IsVirtual():
        Sleep(110)
    poskp = getposition()
    if not (posfh["chicang"] ==0) and poskp["position"]:
        while (not ordida) and ((posfh["position"][0]["Amount"]==poskp["position"][0]["Amount"]) and poskp["position"][0]["FrozenAmount"]==0) :
            if (not IsVirtual()) :
                Sleep(110)
            ordida = exchange.Sell(conprice, connum)
            poskp = getposition()
            if not (posfh["chicang"] ==0) :
                break
    ext.PlotFlag(time.time(), "平多", "平多", "flag", "green")
    if not IsVirtual():
        Sleep(110)
    Log("价格",conprice,"平多",connum,"张，订单已下@")
    return ordida

def findOrder (orderId, NumOfTimes, ordersList = []) :
    for j in range(NumOfTimes) :
        orders = None
        if len(ordersList) == 0:
            orders = _C(exchange.GetOrders)
        else :
            orders = ordersList
        for i in range(len(orders)):
            if orderId == orders[i]["Id"]:
                return True
        Sleep(1000)
    return False

def cancelOrder (price, orderType) :
    orders = _C(exchange.GetOrders)
    for i in range(len(orders)) : 
        if price == orders[i]["Price"] and orderType == orders[i]["Type"]: 
            exchange.CancelOrder(orders[i]["Id"])
            Sleep(500)

def cancelallorders():
    orders = _C(exchange.GetOrders)
    Log('取消所有未成交订单',orders)
    while orders:
        for orderid in orders:
            exchange.CancelOrder(orderid['Id'])
            Sleep(200)
        orders = _C(exchange.GetOrders)
        Sleep(300)

def checkOpenOrders (orders, ticker) :
    global arrNet, arrMsg,orderbreakgrid
    posfh = getposition()
    for i in range(len(arrNet)) : 
        #挂单未成交，取消挂单
        # if findOrder(arrNet[i]["id"], 1, orders) and arrNet[i]["state"] == "pending" :
        #     if arrNet[i]['waitnum']<=50:
        #         arrNet[i]['waitnum'] = arrNet[i]['waitnum'] + 1
        #     else :
        #         exchange.CancelOrder(arrNet[i]["id"])
        #         Sleep(500)
        #         arrNet[i]['waitnum'] = 0
        #         arrNet[i]["state"] = "idle"
        #         Log(i,'号网格买单长时间未成交，将进行撤单。',arrNet[i], "节点平仓，重置为空闲状态。", "#FF0000")

    #挂单成交后立即开平仓单
        if not findOrder(arrNet[i]["id"], 1, orders) and arrNet[i]["state"] == "pending" :
            orderId = exclosebuy(arrNet[i]["coverPrice"], arrNet[i]["amount"],posfh)
            if orderId :
                arrNet[i]["state"] = "cover"
                arrNet[i]["id"] = orderId 
                Log(i,'号网格平仓单已下单')               
            else :
                # 撤销
                cancelOrder(arrNet[i]["coverPrice"], ORDER_TYPE_SELL)
                arrMsg.append("挂单失败!" + json.dumps(arrNet[i]) + ", time:" + _D())
            arrNet[i]['waitnum'] = 0

def checkCoverOrders (orders, ticker) :
    global arrNet, arrMsg
    for i in range(len(arrNet)) : 
        if not findOrder(arrNet[i]["id"], 1, orders) and arrNet[i]["state"] == "cover" :
            arrNet[i]["id"] = -1
            arrNet[i]["state"] = "idle"
            arrNet[i]["tradnum"] +=1
            Log(arrNet[i], i,"号节点平仓，重置为空闲状态。", "#FF0000")

def checkbreakorders () :
    global orderbreakgrid
    order = _C(exchange.GetOrder,orderbreakgrid[0]['id'])
    Sleep(100)
    if orderbreakgrid[0]['state'] == 'xiandanp':        
        if order["Status"] == 1:
            Log("对冲平仓订单已经全部成交@","#FF0000")          
            orderbreakgrid[0]['id'] = 0
            orderbreakgrid[0]['price'] = 0
            orderbreakgrid[0]['amount'] = 0
            orderbreakgrid[0]['state'] = 'free'
        if order["Status"] == 3:
            Log(order)
            Log('平仓订单为未知状态，策略将停止，请人工确认订单状态@')
            onexit()            

def onexit():
    Log('策略即将停止')

def doorder():
    global orderbreakgrid
    order = _C(exchange.GetOrder,orderbreakgrid[0]['id'])
    Sleep(100)
    if orderbreakgrid[0]['state'] == 'xiandan':        
        if order["Status"] == 1:
            Log("对冲订单已经全部成交@")
            orderbreakgrid[0]['state'] = 'chicang'
        if order["Status"] == 3:
            Log(order)
            Log('订单为未知状态，策略将停止，请人工确认订单状态@')
            onexit()

        if order['Status']== 0: #1已完成，0未完成，2已经取消，3未知
            exchange.CancelOrder(orderbreakgrid[0]['id'])
            Sleep(100)
            order = _C(exchange.GetOrder,orderbreakgrid[0]['id'])
            weicjnum = order.Amount - order.DealAmount
            if order["Status"] == 1:
                Log("对冲订单已经全部成交@")
                orderbreakgrid[0]['state'] = 'chicang'
            if order["Status"] == 3:
                Log(order)
                Log('订单为未知状态，策略将停止，请人工确认订单状态@')
                onexit()
            if order['Status']== 2 and orderbreakgrid[0]['state'] =='xiandan': #1已完成，0未完成，2已经取消，3未知
                Log("对冲订单已取消,将进行补单循环。@")
                while orderbreakgrid[0]['state'] == 'xiandan' and order['Status'] == 2:
                    ticker = _C(exchange.GetTicker)            
                    acc = _C(exchange.GetAccount)
                    orderiddc = exsell(ticker.Buy, weicjnum, acc) # 补挂对冲单,开空
                    if orderiddc:
                        orderbreakgrid[0]['id'] = orderiddc
                        orderbreakgrid[0]['price'] = ticker.Buy
                        orderbreakgrid[0]['state'] = 'xiandan'
                    order = _C(exchange.GetOrder,orderbreakgrid[0]['id'])
                    if order["Status"] == 1:
                        Log("对冲订单已经全部成交@")
                        orderbreakgrid[0]['state'] = 'chicang'
                    if order["Status"] == 3:
                        Log(order)
                        Log('订单为未知状态，策略将停止，请人工确认订单状态@')
                        onexit()
                    if order['Status']== 0: #1已完成，0未完成，2已经取消，3未知
                        exchange.CancelOrder(orderbreakgrid[0]['id'])
                        Sleep(100)
                        order = _C(exchange.GetOrder,orderbreakgrid[0]['id'])
                        weicjnum = order.Amount - order.DealAmount
                        if order["Status"] == 1:
                            Log("对冲订单已经全部成交@")
                            orderbreakgrid[0]['state'] = 'chicang'
                        if order["Status"] == 3:
                            Log(order)
                            Log('订单为未知状态，策略将停止，请人工确认订单状态@')
                            onexit()
    if orderbreakgrid[0]['state'] == 'xiandanp':        
        if order["Status"] == 1:
            Log("对冲平仓订单已经全部成交@")
            orderbreakgrid[0]['id'] = 0
            orderbreakgrid[0]['price'] = 0
            orderbreakgrid[0]['amount'] = 0
            orderbreakgrid[0]['state'] = 'free'
        if order["Status"] == 3:
            Log(order)
            Log('平仓订单为未知状态，策略将停止，请人工确认订单状态@')
            onexit()            
        if order['Status']== 0: #1已完成，0未完成，2已经取消，3未知
            exchange.CancelOrder(orderbreakgrid[0]['id'])
            Sleep(100)
            order = _C(exchange.GetOrder,orderbreakgrid[0]['id'])
            weicjnum = order.Amount - order.DealAmount
            if order["Status"] == 1:
                Log("对冲平仓订单已经全部成交@")
                orderbreakgrid[0]['id'] = 0
                orderbreakgrid[0]['price'] = 0
                orderbreakgrid[0]['amount'] = 0
                orderbreakgrid[0]['state'] = 'free'
            if order["Status"] == 3:
                Log(order)
                Log('平仓订单为未知状态，策略将停止，请人工确认订单状态@')
                onexit()
            if order['Status']== 2 and orderbreakgrid[0]['state'] =='xiandanp': #1已完成，0未完成，2已经取消，3未知
                Log("对冲订单已取消,将进行补单循环。@")
                while orderbreakgrid[0]['state'] == 'xiandanp' and order['Status'] == 2:
                    ticker = _C(exchange.GetTicker)            
                    posfh = getposition()
                    orderiddc = exclosesell(ticker.Sell,weicjnum,posfh) #平对冲单
                    if orderiddc:
                        orderbreakgrid[0]['id'] = orderiddc
                        orderbreakgrid[0]['price'] = ticker.Buy
                        orderbreakgrid[0]['state'] = 'xiandanp'
                    order = _C(exchange.GetOrder,orderbreakgrid[0]['id'])
                    if order["Status"] == 1:
                        Log("对冲平仓订单已经全部成交@")
                        orderbreakgrid[0]['id'] = 0
                        orderbreakgrid[0]['price'] = 0
                        orderbreakgrid[0]['amount'] = 0
                        orderbreakgrid[0]['state'] = 'free'
                    if order["Status"] == 3:
                        Log(order)
                        Log('平仓订单为未知状态，策略将停止，请人工确认订单状态@')
                        onexit()
                    if order['Status']== 0: #1已完成，0未完成，2已经取消，3未知
                        exchange.CancelOrder(orderbreakgrid[0]['id'])
                        Sleep(100)
                        order = _C(exchange.GetOrder,orderbreakgrid[0]['id'])
                        weicjnum = order.Amount - order.DealAmount
                        if order["Status"] == 1:
                            Log("对冲平仓订单已经全部成交@")
                            orderbreakgrid[0]['id'] = 0
                            orderbreakgrid[0]['price'] = 0
                            orderbreakgrid[0]['amount'] = 0
                            orderbreakgrid[0]['state'] = 'free'
                        if order["Status"] == 3:
                            Log(order)
                            Log('平仓订单为未知状态，策略将停止，请人工确认订单状态@')
                            onexit()
def getorder(orderid) :
    if (not IsVirtual()) :
        orderstate = _C(exchange.GetOrder,orderid)
        while not orderstate :
            Sleep(150)
            orderstate = _C(exchange.GetOrder,orderid)
    else :
        orderstate = _C(exchange.GetOrder,orderid)
        while not orderstate :
            Sleep(150)
            orderstate = _C(exchange.GetOrder,orderid)
    #record.pop()
    return orderstate

def pingcang (ticker):
    global arrNet, orderbreakgrid
    solidprice = 0.001
    Sleep(100)
    posfh = getposition()
    if posfh["position"]:
        for i in range(len(posfh["position"])) :
            #平空头仓位
            if posfh["position"]:
                if posfh["position"][i]["Type"] == 1 : 
                    ordidp = exclosesell(ticker.Last*(1+solidprice),posfh["position"][i]["Amount"],posfh)
                    if ordidp :
                        ordidafh = getorder(ordidp)
                        while ordidafh["Status"] == 0 :
                            exchange.CancelOrder(ordidp)
                            Sleep(100)
                            ordidafh = getorder(ordidp)
                            weicjnum = ordidafh.Amount - ordidafh.DealAmount
                            if ordidafh["Status"] == 1:
                                Log("对冲平仓订单已经全部成交@")                            
                            if ordidafh["Status"] == 3:
                                Log(ordidafh)
                                Log('平仓订单为未知状态，策略将停止，请人工确认订单状态@')
                                onexit()
                            if ordidafh["Status"] == 2:
                                ticker = _C(exchange.GetTicker)            
                                posfh1 = getposition()
                                ordidp = exclosesell(ticker.Last*(1+solidprice),weicjnum,posfh1) #平对冲单
                                ordidafh = getorder(ordidp)
                                Log('平空订单已下。')
                                if ordidafh["Status"] == 3:
                                    Log(ordidafh)
                                    Log('平仓订单为未知状态，策略将停止，请人工确认订单状态@')
                                    onexit()
                            Log(ordidafh["Status"]) 
                                                    
                        if ordidafh["Status"] == 1 :
                            orderbreakgrid[0]['id'] = 0
                            orderbreakgrid[0]['price'] = 0
                            orderbreakgrid[0]['amount'] = 0
                            orderbreakgrid[0]['state'] = 'free'
                            Log('空单平仓完成')
                        if ordidafh["Status"] ==3:
                            Log(ordidp)
                            Log('空单平仓订单为状态异常，策略将停止，请人工确认订单状态@')
                            onexit()
            if posfh["position"]:
                #平多头仓位
                if posfh["position"][i]["Type"] == 0 : 
                    Log(posfh["position"][i]) 
                    ordidp = exclosebuy(ticker.Last*(1-solidprice), posfh["position"][i]["Amount"],posfh)
                    if ordidp :
                        ordidafh = getorder(ordidp)
                        while ordidafh["Status"] == 0 :
                            exchange.CancelOrder(ordidp)
                            Sleep(100)
                            ordidafh = getorder(ordidp)
                            weicjnum = ordidafh.Amount - ordidafh.DealAmount
                            if ordidafh["Status"] == 1:
                                Log("网格平多仓订单已经全部成交@")                            
                            if ordidafh["Status"] == 3:
                                Log(ordidafh)
                                Log('平多仓订单为未知状态，策略将停止，请人工确认订单状态@')
                                onexit()
                            if ordidafh["Status"] == 2:
                                ticker = _C(exchange.GetTicker)            
                                posfh1 = getposition()
                                ordidp = exclosebuy(ticker.Last*(1-solidprice), weicjnum,posfh1)
                                ordidafh = getorder(ordidp)
                                Log('平多订单已下。')
                                if ordidafh["Status"] == 3:
                                    Log(ordidafh)
                                    Log('平多仓订单为未知状态，策略将停止，请人工确认订单状态@')
                                    onexit()   
                        if ordidafh["Status"] ==1 :   #1已完成，0未完成，2已经取消，3未知                     
                            for i in range(len(arrNet)) :                             
                                arrNet[i]["id"] = -1
                                arrNet[i]["state"] = "idle"
                                Log(arrNet[i], "节点平仓，重置为空闲状态。", "#FF0000")
                            Log('多单平仓完成')
                        if ordidafh["Status"] ==3:
                            Log(ordidp)
                            Log('多单平仓订单为状态异常，策略将停止，请人工确认订单状态@')
                            onexit()


def dynyingkui():
    global upgrid
    mianzhi = 100
    postions = getposition()["position"]
    ticker = _C(exchange.GetTicker)
    account = _C(exchange.GetAccount)
    if postions :
        fudongyksum = 0
        Margindcsum = 0
        if IsVirtual() :
            fudongykdc = 0
            fudongykkc = 0
            for i in range(len(postions)):
                if postions[i]["Type"] ==0:
                    fudongykdc = (postions[i]["Amount"] * mianzhi / postions[i]["Price"] -
                                postions[i]["Amount"] * mianzhi / ticker["Last"])
                    Margindcsum = Margindcsum + postions[i]["Margin"]         
                else :
                    fudongykkc = (postions[i]["Amount"] * mianzhi / ticker["Last"] -
                                postions[i]["Amount"] * mianzhi / postions[i]["Price"])
            fudongyksum = fudongykdc + fudongykkc
            #Log('多+空',fudongykdc,fudongykkc,fudongykdc + fudongykkc,Margindcsum)     
        else :
            if "Huobi" in exname :
                zhanghuquanyi = float(account["Info"]["margin_balance"])
            if "OKCoin" in exname :
                zhanghuquanyi = float(account["Info"]["equity"])
        #对冲单盈利覆盖网格亏损将进行平仓，并激活更新网格参数
        if fudongyksum > 0 :
            Log('对冲仓位盈利已覆盖网格亏损,将全部平仓,并更新网格')
            cancelallorders()
            pingcang(ticker)
            upgrid = True 


            


def onTick () :
    global arrNet, arrMsg, acc,orderbreakgrid,upgrid,lend,newbard,xiumian,xiumianstart,xiumianrestart,jiacang

    ticker = _C(exchange.GetTicker)    # 每次获取当前最新的行情
    #休眠重启将平对冲单
    if xiumianrestart :
        Log('休眠后重启，将平对冲单，并下网格平仓单')
        posfh = getposition()
        #以现价平对冲单
        orderiddc = exclosesell(ticker.Last,orderbreakgrid[0]['amount'],posfh) #平对冲单
        if orderiddc:
            orderbreakgrid[0]['id'] = orderiddc
            orderbreakgrid[0]['price'] = ticker.Last
            orderbreakgrid[0]['state'] = 'xiandanp'
        #处理对冲仓位平仓单
        doorder()
        #重新检查网格平仓单，有持仓的网格下平仓挂单
        orders = _C(exchange.GetOrders)    
        checkOpenOrders(orders, ticker)
        Log('原网格持仓，平仓单已重新下单完成')
        xiumianrestart = False        

    for i in range(len(arrNet)):       # 遍历所有网格节点，根据当前行情，找出需要挂单的位置，挂买单。
        if i != len(arrNet) - 1 and arrNet[i]["state"] == "idle" and ticker.Last > arrNet[i]["price"] and ticker.Last < arrNet[i + 1]["price"]:
            acc = _C(exchange.GetAccount)
            if acc.Stocks < minBalance :     # 如果钱不够了，只能跳出，什么都不做了。
                arrMsg.append("资金不足" + json.dumps(acc) + "！" + ", time:" + _D())
                break

            orderId = exbuy(arrNet[i]["price"], arrNet[i]["amount"], acc) # 挂买单
            Log('第',i,'号网格已下单')
            if orderId : 
                arrNet[i]["state"] = "pending"   # 如果买单挂单成功，更新网格节点状态等信息
                arrNet[i]["id"] = orderId
            else :
                # 撤单
                cancelOrder(arrNet[i]["price"], ORDER_TYPE_BUY)    # 使用撤单函数撤单
                arrMsg.append("挂单失败!" + json.dumps(arrNet[i]) + ", time:" + _D())
    Sleep(200)
    orders = _C(exchange.GetOrders)    
    checkOpenOrders(orders, ticker)    # 检测所有买单的状态，根据变化做出处理。
    Sleep(200)
    orders = _C(exchange.GetOrders)    
    checkCoverOrders(orders, ticker)   # 检测所有卖单的状态，根据变化做出处理。
    
    #下破网格时，开反向对冲单,1分钟K线检查一次
    chicang = 0
    if ticker.Last<arrNet[0]['price'] and orderbreakgrid[0]['id'] == 0 : 
        records = getrecords(PERIOD_M1) #PERIOD_M1
        if not (records.Time[len(records)-1]==lend) :  #交易所bar时间标记为utc8秒时间戳，以开盘价（open）时标记
            newbard = True
            lend = records.Time[len(records)-1]
        if newbard :
            Log('价格低于最低网格，将进行对冲锁仓。',ticker.Last,arrNet[0]['price']) 
            #撤销未成交挂单,并将网格订单状态改为pending，重启后检查订单，重新下平仓单
            cancelallorders()
            for i in range(len(arrNet)):
                if arrNet[i]["state"] == "cover" :
                    arrNet[i]["state"] = "pending"
                    chicang = chicang + arrNet[i]["amount"]
            chicang = duichongxs*chicang
            acc = _C(exchange.GetAccount)
            if chicang == 0:
                Log('价格低于最低网格且持仓为空，将更新网格。')
                cancelallorders() 
                Sleep(200)
                if getposition()['chicang']==0 :
                    for i in range(len(arrNet)): 
                        arrNet[i]["id"] = -1
                        arrNet[i]["state"] = "idle"
                        Log(arrNet[i], i,"号节点平仓，重置为空闲状态。", "#FF0000")
                else:
                    pingcang(ticker)               
                upgrid = True
            if ticker.Buy!=0 and chicang !=0:
                orderiddc = exsell(ticker.Buy, chicang, acc) # 挂对冲单,开空 
                breakgridinf['numkdc'] += 1
                breakgriddate.append({'breakprice':arrNet[0]['price'],'time':_D(ticker.Time/1000),'mode':None,'dealtime':None,'pricegridrange':None})       
                if orderiddc:
                    orderbreakgrid[0]['id'] = orderiddc
                    orderbreakgrid[0]['price'] = ticker.Buy
                    orderbreakgrid[0]['amount'] = chicang
                    orderbreakgrid[0]['state'] = 'xiandan'            
                doorder() #检查订单，未成交的订单进行补单。
                newbard = False
                posfh = getposition()
                Log('对冲仓位已经建立，策略将进入休眠，持仓状态:',posfh)
                xiumian = True
                xiumianstart = ticker.Time   
    
    #价格突破网格顶部平仓价，并且持仓为空，激活更新网格参数
    if ticker.Last>arrNet[len(arrNet)-1]['coverPrice'] and getposition()['chicang']==0:
        Log('价格突破网格顶部平仓价且持仓为空，将更新网格。')
        cancelallorders()
        Sleep(200)
        if getposition()['chicang']==0 :
            for i in range(len(arrNet)): 
                arrNet[i]["id"] = -1
                arrNet[i]["state"] = "idle"
                Log(arrNet[i], i,"号节点平仓，重置为空闲状态。", "#FF0000")
        else:
            pingcang(ticker)        
        upgrid = True     

    # 以下为构造状态栏信息，可以查看FMZ API 文档。
    tbl = {
        "type" : "table", 
        "title" : "网格状态",
        "cols" : ["节点索引", "详细信息"], 
        "rows" : [], 
    }    

    for i in range(len(arrNet)) : 
        tbl["rows"].append([i, json.dumps(arrNet[i])])

    errTbl = {
        "type" : "table", 
        "title" : "记录",
        "cols" : ["节点索引", "详细信息"], 
        "rows" : [], 
    }

    orderTbl = {
     	"type" : "table", 
        "title" : "orders",
        "cols" : ["节点索引", "详细信息"], 
        "rows" : [],    
    }
    breakgridtbl = {
     	"type" : "table", 
        "title" : "破网信息",
        "cols" : ["节点索引", "详细信息",'次数汇总'], 
        "rows" : [],    
    }

    while len(arrMsg) > 20 : 
        arrMsg.pop(0)

    for i in range(len(arrMsg)) : 
        errTbl["rows"].append([i, json.dumps(arrMsg[i])])    

    for i in range(len(orders)) : 
        orderTbl["rows"].append([i, json.dumps(orders[i])])
    for i in range(len(breakgriddate)) : 
        breakgridtbl["rows"].append([i, json.dumps(breakgriddate[i]),json.dumps(breakgridinf)])  

    LogStatus(_D(), "\n", acc, "\n", "arrMsg length:", len(arrMsg),"\n","`" + json.dumps([tbl, errTbl, orderTbl,breakgridtbl]) + "`")

def getrecords(period) :
    congxinhuoqu = False
    if (not IsVirtual()) :
        record = _C(exchange.GetRecords,period)
        while (json.dumps(record) == '{}' or record == None) or congxinhuoqu:
            Sleep(150)
            for i in range(len(record)) :
                if not record[i] :
                    congxinhuoqu = True
                    break
                else :
                    congxinhuoqu = False
            record = _C(exchange.GetRecords,period)
    else :
        record = _C(exchange.GetRecords,period)
        while (json.dumps(record) == '{}' or record == None) or congxinhuoqu:
            Sleep(150)
            for i in range(len(record)) :
                if not record[i] :
                    congxinhuoqu = True
                    break
                else :
                    congxinhuoqu = False
            record = _C(exchange.GetRecords,period)
    return record

def main ():         # 策略执行从这里开始
    global arrNet,orderbreakgrid,upgrid,xiumian,xiumianstart,xiumianrestart,jiacang
    newbar = False
    tradgoon = False
    len0 = 0
    macha = 0
    SetErrorFilter("502:|503:|tcp|character|unexpected|network|timeout|WSARecv|Connect|GetAddr|no such|reset|http|received|EOF|reused")
    exchange.SetTimeout(15000) #exchanges请求超时15秒
    exchange.SetMarginLevel(10)
    exchange.SetContractType(["quarter", "next_week","swap"][0]); #0="quarter",1=next_week
    exname = exchange.GetName()

    records = getrecords(PERIOD_M30) #PERIOD_M30
    ma30 = 0
    if len(records)>=50:
        ma30 = talib.EMA(records.Low,malength)
        ma30 = ma30[-1]
        tradgoon = True
    else:
        Log('基准K线长度不足,不进行交易循环')
        tradgoon = False
    beginPrice = ma30-ma30*griddownrate/100
    for i in range(gridnum):        # for 这个循环根据参数构造了网格的数据结构，是一个列表，储存每个网格节点，每个网格节点的信息如下：
        arrNet.append({
            "price" : beginPrice + i * beginPrice* distance/1000,                    # 该节点的价格
            "amount" : amount,                                      # 订单数量
            "state" : "idle",    # pending / cover / idle           # 节点状态
            "coverPrice" : (beginPrice + i * beginPrice* distance/1000)*(1+pointProfit/1000), # 节点平仓价格
            "id" : -1,                                              # 节点当前相关的订单的ID
            "waitnum":0,
            "tradnum":0,
        })
    orderbreakgrid.append({
        'price':0,
        'amount':0,
        'id':0,
        'state':'free'
    })
    
    while True:    # 构造好网格数据结构后，进入策略主要循环        
        # records = getrecords(PERIOD_M30) #PERIOD_M30
        # if not (records.Time[len(records)-1]==len0) :  #交易所bar时间标记为utc8秒时间戳，以开盘价（open）时标记
        #     newbar = True
        #     len0 = records.Time[len(records)-1]
        # if newbar :
        #     if len(records)>=100:
        #         ma30 = talib.EMA(records.Low,90)
        #         ma30 = ma30[len(ma30)-1]
        #     else:
        #         ma30 = records.Low[len(records)-1]
        #     beginPrice = ma30-ma30*griddownrate
        #     ext.PlotRecords(records,'K线图')
        #     ext.PlotLine('beginPrice',beginPrice)
        #     newbar = False   
         
        if not tradgoon :
            Log('基准K线不足，休眠等待')
            Sleep(30*60*1000)           
        records = getrecords(PERIOD_M30) #PERIOD_M30
        Sleep(200)
        records5 = getrecords(PERIOD_M1) #PERIOD_M30
        if len(records)>=50:
            mal = talib.EMA(records5.Close,30)
            mas = talib.EMA(records5.Close,5)
            macha = (mal[-1] - mas[-1])/records.Close[-1]*100
            ma30 = talib.EMA(records.Low,malength)                               
            ma30 = ma30[-1]
            atr = talib.ATR(records5.High,records5.Low,records5.Close,14)
            ma10 = talib.EMA(records.Close,10)
            atrc = atr[-1]/ma10[-1]*100
            tradgoon = True
            if atrc > 0.2 and macha > 0.5:
                Log('下跌趋势中，停止加仓')
                jiacang = False
            else :
                if not jiacang :
                    Log('下跌趋势回归正常，继续正常加仓。')
                    jiacang = True
        else :
            Log('基准K线长度不足,不进行交易循环')
            tradgoon = False        
        if upgrid :
            beginPrice = ma30-ma30*griddownrate/100
            for i in range(gridnum):        # for 这个循环根据参数构造了网格的数据结构，是一个列表，储存每个网格节点，每个网格节点的信息如下：
                if beginPrice:
                    arrNet[i]['price']=beginPrice + i * beginPrice* distance/1000
                    arrNet[i]['coverPrice']=(beginPrice + i * beginPrice* distance/1000)*(1+pointProfit/1000)
            Log('网格更新成功,开始价格',beginPrice)
            upgrid = False        

        if tradgoon and (not xiumian):    
            onTick()   # 主循环上的处理函数，主要处理逻辑
        if xiumian:
            Sleep(10*60*1000)  
            ticker = _C(exchange.GetTicker)    # 每次获取当前最新的行情          
            xiumiantimedis = ticker.Time - xiumianstart
            if xiumiantimedis > xiumiandis*24*60*60*1000 :
                Log('休眠时间满足，等待市场状态确认。')                
                records = getrecords(PERIOD_M30) #PERIOD_M30
                if len(records)>=50:
                    atr = talib.ATR(records.High,records.Low,records.Close,14)
                    ma10 = talib.EMA(records.Close,10)
                    atrc = atr[-1]/ma10[-1]*100
                if ticker.Last < arrNet[0]['price'] :
                    if atrc < 2 :
                        Log('休眠期满且价格低于底部网格且ATR回归，将更新网格')
                        xiumian = False
                        xiumianrestart = True
                        upgrid = True
                        ma30 = talib.EMA(records.Low,malength)[-1]
                        beginPrice = ma30-ma30*(griddownrate)/100
                        pricegridrange = (ticker.Last - beginPrice)/beginPrice*100
                        breakgridinf['numxgx'] +=1                        
                        breakgriddate[-1]['mode'] = 'downupdate '
                        breakgriddate[-1]['dealtime'] = _D(ticker.Time/1000)
                        breakgriddate[-1]['pricegridrange'] = pricegridrange
                        
                    else :
                        Log('休眠期满且价格低于底部网格，但ATR较高将继续等待')                   
                    
                if ticker.Last > arrNet[-1]['coverPrice'] :
                    if atrc < 2 :
                        Log('休眠期满且价格高于网格顶部平仓线且ATR回归，将更新网格')
                        xiumian = False
                        xiumianrestart = True
                        upgrid = True
                        ma30 = talib.EMA(records.Low,malength)[-1]
                        beginPrice = ma30-ma30*(griddownrate)/100
                        pricegridrange = (ticker.Last - beginPrice)/beginPrice*100
                        breakgridinf['numsgx'] +=1
                        breakgriddate[-1]['mode'] = 'upupdate'
                        breakgriddate[-1]['dealtime'] = _D(ticker.Time/1000)
                        breakgriddate[-1]['pricegridrange'] = pricegridrange
                    else :
                        Log('休眠期满且价格高于网格顶部平仓线，但ATR较高将继续等待')
                if ticker.Last>arrNet[0]['price'] and ticker.Last < arrNet[-1]['coverPrice']:
                    if atrc < 2 :
                        Log('休眠期满且价格在原网格内且ATR回归，策略将继续原网格')
                        xiumian = False
                        xiumianrestart = True
                        pricegridrange = (ticker.Last - arrNet[0]['price'])/arrNet[0]['price']*100
                        breakgridinf['numbgx'] +=1
                        breakgriddate[-1]['mode'] = 'keep'
                        breakgriddate[-1]['dealtime'] = _D(ticker.Time/1000)
                        breakgriddate[-1]['pricegridrange'] = pricegridrange
                    else :
                        Log('休眠期满且价格在原网格内，但ATR较高将继续等待')

        Sleep(500) # 控制轮询频率