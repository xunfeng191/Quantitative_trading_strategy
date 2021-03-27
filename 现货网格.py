# fmz@1ece1e81835bec097ce6ae8a604f2205

#策略设计用作币安火币稳定币交易对网格交易，需要交易币对为0手续费

import json
import urllib.request
import math
import time


# 参数
#beginPrice = 5000
#endPrice = 8000
#distance = 20

pointProfit = 0.0002
amount = 20

# 全局变量
tradegoon = False
arrNet = []
arrMsg = []
acc = None
exorders = None
exticker = None
timedis = 0
acctimedis = 0
tickertimedis = 0
exchange_info = json.loads(urllib.request.urlopen("https://api.binance.com/api/v3/exchangeInfo").read().decode('utf-8'))

trade_info = {} #交易对信息
trade_symbol = baseAsset+quoteAsset

Gridsnum = (endPrice-beginPrice)/distance

def onexit():
    Log("策略停止")
exchange.SetCurrency(baseAsset+"_"+quoteAsset)
ti = _C(exchange.GetTicker)
acc = _C(exchange.GetAccount)
needvalues = amount*ti["Last"]*2
accbalance = _N(acc["Balance"]+acc["FrozenBalance"]+(acc["Stocks"]+acc["FrozenStocks"])*ti["Last"],3)
if accbalance<needvalues*1.1:
    Log("账户起始资产不足，需要",needvalues*1.1,quoteAsset)
    onexit()

for ei in  exchange_info["symbols"]:
  trade_info[ei["symbol"]] = {    
    #最小数量下限
    "minQty": 0,
    #数量小数位数
    "amountSize": 0,
    #价格小数位数
    "priceSize": 0,
    #价格精度
    "tickSize": 0,
    #最小下单价值
    "minvalues":0
  }
  
  for fi in ei["filters"]:
    if (fi["filterType"]=="LOT_SIZE"):
      trade_info[ei["symbol"]]["minQty"] = float(fi["minQty"])
      trade_info[ei["symbol"]]["amountSize"] = int(math.log10(1.1 / float(fi["stepSize"])))
    
    if (fi["filterType"]=="PRICE_FILTER"):
      trade_info[ei["symbol"]]["priceSize"] = int(math.log10(1.1 / float(fi["tickSize"])))        
      trade_info[ei["symbol"]]["tickSize"] = float(fi["tickSize"])
    
    if (fi["filterType"]=="MIN_NOTIONAL"):
      trade_info[ei["symbol"]]["minvalues"] = float(fi["minNotional"])
    
Log("交易对信息",trade_info[trade_symbol])

if _G("arrNet") and (not resetkv):
    arrNet = _G("arrNet")
else:
    for i in range(int((endPrice - beginPrice) / distance)):
        arrNet.append({
            "price" : _N(beginPrice + i * distance,trade_info[trade_symbol]["priceSize"]),
            "amount" : amount,
            "state" : "idle",    # pending / cover / idle
            "coverPrice" : _N(beginPrice + i * distance + pointProfit,trade_info[trade_symbol]["priceSize"]) ,
            "id" : -1,
        })
        _G("arrNet", arrNet) 

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
        Sleep(100)
    return False

def cancelallOrder () :
    orders = _C(exchange.GetOrders)
    for i in range(len(orders)) : 
        exchange.CancelOrder(orders[i]["Id"])
        Sleep(20)

def cancelOrder (price, orderType) :
    orders = _C(exchange.GetOrders)
    for i in range(len(orders)) : 
        if price == orders[i]["Price"] and orderType == orders[i]["Type"]: 
            exchange.CancelOrder(orders[i]["Id"])
            Sleep(20)

def checkOpenOrders (orders, ticker) :
    global arrNet, arrMsg, tradegoon
    for i in range(len(arrNet)) : 
        if not findOrder(arrNet[i]["id"], 1, orders) and arrNet[i]["state"] == "pending" and tradegoon:
            orderId = exchange.Sell(arrNet[i]["coverPrice"], arrNet[i]["amount"], arrNet[i], ticker)
            if orderId :
                arrNet[i]["state"] = "cover"
                arrNet[i]["id"] = orderId                
            else :
                # 撤销
                cancelOrder(arrNet[i]["coverPrice"], ORDER_TYPE_SELL)
                arrMsg.append("挂单失败!" + json.dumps(arrNet[i]) + ", time:" + _D())
            _G("arrNet", arrNet)

def checkCoverOrders (orders, ticker) :
    global arrNet, arrMsg
    for i in range(len(arrNet)) : 
        if not findOrder(arrNet[i]["id"], 1, orders) and arrNet[i]["state"] == "cover" :
            arrNet[i]["id"] = -1
            arrNet[i]["state"] = "idle"
            Log(arrNet[i], "节点平仓，重置为空闲状态。", "#FF0000")
            _G("arrNet", arrNet)


def onTick () :
    global arrNet, arrMsg, acc, exorders, tradegoon,tickertimedis,acctimedis,exticker
    time0 = time.time()
    exticker = _C(exchange.GetTicker)
    tickertimedis = time.time() - time0
    time0 = time.time()
    acctimedis = time.time() - time0

    for i in range(len(arrNet)):
        if i != len(arrNet) - 1 and arrNet[i]["state"] == "idle" and exticker.Sell > arrNet[i]["price"] and exticker.Sell < arrNet[i + 1]["price"] and tradegoon:
            acc = _C(exchange.GetAccount)
            if acc.Balance < trade_info[trade_symbol]["minvalues"] :
                arrMsg.append("资金不足" + json.dumps(acc) + "！" + ", time:" + _D())
                break

            orderId = exchange.Buy(arrNet[i]["price"], arrNet[i]["amount"], arrNet[i], exticker)
            if orderId : 
                arrNet[i]["state"] = "pending"
                arrNet[i]["id"] = orderId
            else :
                # 撤单
                cancelOrder(arrNet[i]["price"], ORDER_TYPE_BUY)
                arrMsg.append("挂单失败!" + json.dumps(arrNet[i]) + ", time:" + _D())
            _G("arrNet", arrNet)
    Sleep(100)
    exorders = _C(exchange.GetOrders)
    checkOpenOrders(exorders, exticker)
    Sleep(500)
    exorders = _C(exchange.GetOrders)
    checkCoverOrders(exorders, exticker)

    
    LogProfit(_N(acc["Balance"]+acc["FrozenBalance"]+(acc["Stocks"]+acc["FrozenStocks"])*exticker["Last"]-startcoin,3) ,'&')

def updatestatus():
    global arrNet, arrMsg, acc, exorders,timedis,exticker
    
    tbl = {
        "type" : "table", 
        "title" : "网格状态",
        "cols" : ["序号", "买入价格","交易数量","订单状态","卖出价格","订单编号","最新价格"], 
        "rows" : [], 
    }    

    for i in range(len(arrNet)) : 
        tbl["rows"].append([i+1, json.dumps(arrNet[i]["price"]), json.dumps(arrNet[i]["amount"]),
        json.dumps(arrNet[i]["state"]), json.dumps(arrNet[i]["coverPrice"]), json.dumps(arrNet[i]["id"]), json.dumps(exticker["Last"])])
    
    tableacc = {
        "type": "table",
        "title": "资产信息",
        "cols": ["交易对","余钱","冻结钱","余币","冻结币"],
        "rows": [],
    };

    tableacc["rows"].append([
        trade_symbol,
        quoteAsset + ":" + str(acc["Balance"]),
        quoteAsset + ":" + str(acc["FrozenBalance"]),
        baseAsset + ":" + str(acc["Stocks"]),
        baseAsset + ":" + str(acc["FrozenStocks"]),
    ]); 

    errTbl = {
        "type" : "table", 
        "title" : "报错记录",
        "cols" : ["节点索引", "详细信息"], 
        "rows" : [], 
    }

    orderTbl = {
     	"type" : "table",
        "title" : "未成交订单簿",
        "cols" : ["序号", "订单ID", "下单价格", "下单数量", "成交数量", "成交均价", "订单状态", "订单类型"], 
        "rows" : [],    
    }

    while len(arrMsg) > 20 : 
        arrMsg.pop(0)

    for i in range(len(arrMsg)) : 
        errTbl["rows"].append([i, json.dumps(arrMsg[i])])    

    for i in range(len(exorders)) : 
        orderTbl["rows"].append([i+1, json.dumps(exorders[i]["Id"]), json.dumps(exorders[i]["Price"]), json.dumps(exorders[i]["Amount"]), 
        json.dumps(exorders[i]["DealAmount"]), json.dumps(exorders[i]["AvgPrice"]), json.dumps(exorders[i]["Status"]), json.dumps(exorders[i]["Type"])])

    LogStatus(_D(), 
    "\n","ticker行情更新延迟:",tickertimedis*1000,"毫秒\n",
    "\n","账户信息更新延迟:",acctimedis*1000,"毫秒\n",
    "\n","循环时间:",timedis*1000,"毫秒\n",
     "`" + json.dumps([tbl, errTbl, orderTbl]) + "`"
    "\n", "`" + json.dumps([tableacc]) + "`")

def clearpos ():
    global acc,tradegoon
    account=_C(exchange.GetAccount);
    acc = account
    ticker = _C(exchange.GetTicker)
    while (account.FrozenStocks != 0 or account.FrozenBalance != 0):
        cancelallOrder()
        Sleep(100) 
        account=_C(exchange.GetAccount);
  
    if (tradegoon):
        while ((account.Stocks+account.FrozenStocks)*ticker["Last"] > trade_info[trade_symbol]["minvalues"]*1.5) :
            exchange.Sell(-1,_N(account.Stocks,trade_info[trade_symbol]["amountSize"]));
            Sleep(100)
            account=_C(exchange.GetAccount);
            while (account.FrozenStocks != 0 or account.FrozenBalance != 0):
                cancelallOrder()
                Sleep(100) 
    updatestatus()
    Log("已全部平仓")
    onexit()

def main ():
    global arrNet,timedis,tradegoon
    SetErrorFilter("502:|503:|tcp|character|unexpected|network|timeout|WSARecv|Connect|GetAddr|no such|reset|http|received|EOF|reused|Unknown");
    exchange.SetTimeout(10000);
    while True:
        time0 = time.time()
        cmd = GetCommand();
        if (cmd == "执行交易策略") :
            tradegoon = True
            Log("交易功能已启动@")
        
        if (cmd == "重置图表") :
            chart.reset(0)
            Log("图表已重置")
        
        if (cmd == "重置利润图表") :
            LogProfitReset(0);
            Log("利润图表已重置")
        
        if (cmd == "全平停止") :
            clearpos()
        if (cmd == "取消所有挂单") :
            cancelallOrder()
            Log("挂单已取消")
        onTick()
        updatestatus()
        Sleep(500)
        timedis = time.time()-time0