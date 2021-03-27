var profitAmount = 0; //总盈利
var initStateStr = "【账号初始情况】\n"; //初始账号信息
var initState;
var orderInfos = []; //成交记录信息
var statusStr = ""; //状态信息
var sellPriceGroup = [];  //卖价数组
var sumSellPrice = 0;
var sellPriceAverage = 0;
var targetBuyPrice = 0;
var targetSellPrice = 0;
var canBuyCount = 0;
var profitDif = 0;
//var buyPriceTrade = 0; //买入价格最终成交价格
var dealTimes = 0; //成交次数
var isWorking = true;
//var copiesNow = 0; //网格次数
var buyPriceGroup = []; //买入价格的组合
var buyNumsGroup=[];//买入数量的组合
var buyTimeGroup=[];//买入的时间组合，用来判断是否下跌过快
//var sellPriceGroup = []; //卖出价格的组合
var basePrice=0; //基价

 
//更新状态栏信息
function updateTableStatus(StrStatus, nowBalance) {
    var tb_manager = $.createTableMgr();
    var tb1 = tb_manager.AddTable("资产信息");
    var tb2 = tb_manager.AddTable("成交信息");

    //账号信息表格
    var tableTitles = ["平台", "持币", "余额", "冻结币", "冻结余额"];
    for (var k = 0; k < exchanges.length; k++) {
        var infoAccount = $.TableInfo();
        for (var i = 0; i < tableTitles.length; i++) {
            infoAccount.push(tableTitles[i], StrStatus[tableTitles.length * k + i]);
        }
        tb1.SetRowByTableInfo(k, infoAccount);
    }

    //成交信息表格
    var orderTableTitles = ["操作", "平台", "成交价格", "数量", "时间", "模式"];
    var orderNum = orderInfos.length / orderTableTitles.length;
    for (var m = 0; m < orderNum; m++) {
        var orderAccount = $.TableInfo();
        for (var l = 0; l < orderTableTitles.length; l++) {
            orderAccount.push(orderTableTitles[l], orderInfos[orderTableTitles.length * (orderNum - m - 1) + l]);
        }
        tb2.SetRowByTableInfo(m, orderAccount);
    }


    if ((orderInfos.length / 6) > 10) {
        orderInfos.splice(0, orderInfos.length - 60);
    }


    var nowTime = new Date().getTime();
    tb_manager.LogStatus(initStateStr + nowBalance, statusStr + "\n【总利润:】" + profitAmount);
}


//获取当前交易所的资产信息
function getExchangesState() {
    var allStocks = 0;
    var allBalance = 0;
    var details = [];
    var exchangeName;
    var fee = TradeFee;
    var StrStatus = [];

    var account = null;
    while (!(account = exchange.GetAccount())) {
        Sleep(TickInterval);
        Log("正在获取交易所账号信息...");
    }

    exchangeName = exchange.GetName();
    StrStatus.push(exchangeName);
    StrStatus.push(account.Stocks);
    StrStatus.push(account.Balance);
    StrStatus.push(account.FrozenStocks);
    StrStatus.push(account.FrozenBalance);

    allStocks += account.Stocks + account.FrozenStocks;
    allBalance += account.Balance + account.FrozenBalance;

    fee = TradeFee;
    details.push({
        exchange: exchange,
        account: account,
        fee: fee,
    });



    var nowStateStr = "【最新状态】总币数：" + allStocks + " 总金额:" + allBalance + "\n"

    //更新状态信息
    updateTableStatus(StrStatus, nowStateStr);


    return {
        allStocks: allStocks,
        allBalance: allBalance,
        details: details
    };
}
//发送邮箱
function sendEmail(mes) {
    Log(mes + "@"); //微信通知
}




//更新价格
function updateStatePrice(state) {
    var getAllPriceSuccess = false; //全部判断才过，如果某一个获取不到，则全部重新获取
    while (!getAllPriceSuccess) {
        var threadGetticker = state.details[0].exchange.Go("GetTicker");
        var ticker = threadGetticker.wait();
        //将手续费加到价格中，手续费也是成本。
        if (ticker !== null) {
            state.details[0].ticker = {
                Buy: (ticker.Buy * (1 - (state.details[0].fee / 100))) - hedgePrice,
                Sell: (ticker.Sell * (1 + (state.details[0].fee / 100)) + hedgePrice)
            };
            state.details[0].realTicker = {
                Buy: ticker.Buy - hedgePrice,
                Sell: ticker.Sell + hedgePrice
            };
            state.details[0].canBuy = _N(state.details[0].account.Balance*9/10/(copies-buyPriceGroup.length) / ticker.Sell,amountScale);
            getAllPriceSuccess = true;
        } else {
            getAllPriceSuccess = false;
        }

    }
}



//标准差计算函数
function biaozhuncha(priceGroup, priceAverage) {
    var fanchaSum = 0;
    for (var m = 0; m < priceGroup.length; m++) {
        fanchaSum = fanchaSum + Math.pow((priceGroup[m] - priceAverage), 2);
    }

    var fancha = fanchaSum / initSumTimes;
    var biaozhuncha = Math.sqrt(fancha);

    return biaozhuncha;

}




function cancelExOrders(exchange) {
    while (true) {
        var orders = null;
        while (!(orders = exchange.GetOrders())) {
            Sleep(Interval);
        }

        if (orders.length == 0) {
            break;
        }

        for (var j = 0; j < orders.length; j++) {
            exchange.CancelOrder(orders[j].Id, orders[j]);
        }
    }
}

//异步下单
//mode:0:买入 1:卖出
function Trade(initState, Detail, tradeAmount, mode) {

    var orderID = null;

    var isFinish = false; //是否完成订单
    var InitPrice = 0;


    //根据mode决定买卖方向
    var ExDirection = "Buy";
    if (mode == 0) {
        ExDirection = "Buy";
        InitPrice = Detail.realTicker.Sell;
    } else if (mode == 1) {
        ExDirection = "Sell";
        InitPrice = Detail.realTicker.Buy;
    }

    //根据交易所支持做小量修改下单量 
    var amount=_N(tradeAmount,amountScale);
    InitPrice=_N(InitPrice,priceScale)
    
    
    var result = Detail.exchange.Go(ExDirection, InitPrice, amount, "委托价:" + InitPrice);

    orderID = result.wait(); //得到订单号  

    var nowState;
    //吃单模式
    //取消未完成的订单，重新下单
    while (!isFinish) {
        Sleep(4 * TickInterval);

        cancelExOrders(Detail.exchange);

        //获取最新的价格，获取最新的账号信息 
        nowState = getExchangesState();
        updateStatePrice(nowState); // 更新 ，并获取 各个交易所行情

        //判断是否完成订单
        if (!isFinish) {
            var newPrice;
            //计算出未完成的交易量 
            var diffMoney = Math.abs(Detail.account.Balance - nowState.details[0].account.Balance - nowState.details[0].account.FrozenBalance);
            var dealAmount = Math.abs(Detail.account.Stocks - nowState.details[0].account.Stocks - nowState.details[0].account.FrozenStocks);
            var doAmount = tradeAmount - dealAmount;

            if (doAmount < Math.pow(0.1,amountScale)) {
                isFinish = true; //完成交易 
                Log("完成交易" + dealAmount);

            } else {
                //未完成交易,取消
                Log("未完成交易,取消委托。总下单" + tradeAmount + "已完成交易：" + dealAmount+",还差"+_N(doAmount,amountScale));
                if (mode == 0) {
                    newPrice = nowState.details[0].realTicker.Sell;
                } else if (mode == 1) {
                    newPrice = nowState.details[0].realTicker.Buy;
                }

                //重新下单  
                 var amount=_N(doAmount,amountScale);
                 result = Detail.exchange.Go(ExDirection, newPrice, amount, "委托价:" + newPrice);

            }

        }


        if (!isFinish) {
            orderID = result.wait(); //得到订单号   
        }



        if (isFinish) {
            //完成全部交易 
            Log("完成全部交易 ");
            break;
        }
    }


    updateStatePrice(getExchangesState()); // 更新 ，并获取 各个交易所行情



    var diffMoneyEnd = Math.abs(Detail.account.Balance - nowState.details[0].account.Balance);
    var dealAmountEnd = Math.abs(Detail.account.Stocks - nowState.details[0].account.Stocks);

    return {
        price: _N(diffMoneyEnd / dealAmountEnd,priceScale),
        amount: _N(dealAmountEnd,amountScale),

    };
}


function putOrderInfo(control, name, price, count, time, type) {
    orderInfos.push(control);
    orderInfos.push(name);
    orderInfos.push(price);
    orderInfos.push(count);
    orderInfos.push(time);
    orderInfos.push(type);
}


/**
* 循环执行核心代码
*/
function onTick() {
    var Sell1Price; //卖一价
    var Buy1Price; //买一价

    var state = getExchangesState();
    updateStatePrice(state); // 更新价格行情,计算排除手续费影响的对冲价格值
    var details = state.details; // 取出 state 中的 details 值 

    Sell1Price = details[0].ticker.Sell;
    Buy1Price = details[0].ticker.Buy;
    
    sellPriceGroup.push(Sell1Price);
    
    //统计数组中的币价的总数
    sumSellPrice = sumSellPrice + Sell1Price;

    //如果已经达到观察次数，则开始
    if (sellPriceGroup.length > initSumTimes) {

        sumSellPrice = sumSellPrice - sellPriceGroup[0];

        sellPriceGroup.shift();
        sellPriceAverage = sumSellPrice / initSumTimes;

        
        if(isAutoSetBaseLine){
            //自动寻找基价=观察期均价下浮n%
            targetBuyPrice = sellPriceAverage*(1-downRate/100); 
        }else{
            //手动寻找基价=手动设置的基价下浮n%
            targetBuyPrice=basePrice*(1-downRate/100);
        }
        
        
        //确定下一阶段目标价格
        if(buyPriceGroup.length>0){
             targetBuyPrice = buyPriceGroup[buyPriceGroup.length-1]*(1-downRate/100);
             targetSellPrice=buyPriceGroup[buyPriceGroup.length-1]*(1+riseRate/100);
        }

 
        //计算下一阶段网格可以成交的数量 
        canBuyCount = _N(details[0].canBuy,amountScale );
          
        
        
        if (buyPriceGroup.length==0&&canBuyCount < Math.pow(0.1,amountScale)) {
            throw "错误:每一份的成交量低于交易所要求的最低成交数量"+ Math.pow(0.1,amountScale)+"，请检查网格份数是否过高或者看下钱够不够";
        }

        
        //判断是否下跌过快，过快则加大触发比例（可在此根据需要增加下跌过快处理）
        if(isAutoAddDownRate){
            if(buyTimeGroup.length>2){
                //3分钟内连续成交2次，则认为下跌过快
                if((buyTimeGroup[buyTimeGroup.length-1]-buyTimeGroup[buyTimeGroup.length-2])<(3*60*1000)){
                    //过快
                    targetBuyPrice=targetBuyPrice*(1-downRate/100);
                }
            }
        }
        
        //是否达到卖出目标
        if (buyPriceGroup.length>0&Buy1Price > targetSellPrice) {
            var tradeInfo = Trade(state, details[0], buyNumsGroup[buyNumsGroup.length-1], 1);
            putOrderInfo("卖出", exchange.GetName(), tradeInfo.price, tradeInfo.amount, _D(new Date().getTime()), "卖出");
 
            var profitThisTime = (tradeInfo.price * _N(tradeInfo.amount,amountScale) * (1 - TradeFee / 100)) - buyPriceGroup[buyPriceGroup.length - 1]*_N(tradeInfo.amount,amountScale) ;
            profitAmount += profitThisTime;
            LogProfit(profitAmount);
            _G("profitAmount", profitAmount);

            sendEmail("卖出价格：" + tradeInfo.price + "数量：" + tradeInfo.amount + "利润：" + profitThisTime + "总利润：" + profitAmount);

            buyTimeGroup.pop();
            buyPriceGroup.pop();
            buyNumsGroup.pop();
            dealTimes++;
         

        } else if ((Sell1Price < targetBuyPrice)&&(buyPriceGroup.length<copies )&&(basePrice!=0||isAutoSetBaseLine)) {
            //达到买入价格
            var tradeInfo = Trade(state, details[0], canBuyCount, 0); 
            buyPriceTrade = tradeInfo.price * tradeInfo.amount * (1 - TradeFee / 100); //用于计算利润
            putOrderInfo("买入", exchange.GetName(), tradeInfo.price, tradeInfo.amount, _D(new Date().getTime()), "买入");
            
            sendEmail("买入价格：" + tradeInfo.price + "数量：" + tradeInfo.amount + "当前利润：" + profitAmount);

            buyPriceGroup.push(tradeInfo.price);
            buyNumsGroup.push(_N(tradeInfo.amount,amountScale));
            buyTimeGroup.push(new Date().getTime());
        } else {
            profitDif = biaozhuncha(sellPriceGroup, sellPriceAverage);//计算标准差
            $.PlotLine('观察周期内的平均价格：', _N(sellPriceAverage,priceScale));

        }
    }


    statusStr = "当前卖一价格：" + _N(Sell1Price,priceScale) + " 买入目标价:" + _N(targetBuyPrice,priceScale) + "标准差:" + profitDif+"\n";
    if(buyPriceGroup.length>0){
        statusStr+="当前买一价格："+ _N(Buy1Price,priceScale)+" 最近目标卖出价："+targetSellPrice+"\n等待卖出仓：【"+buyPriceGroup+"】";
    }
    
    $.PlotLine('卖1价格', _N(Sell1Price,priceScale));


}

 
/**
* 检查策略参数
* 
*/
function checkParmers(){
    if(TickInterval<300){
        throw "轮训时间过短,请重新设置";    
    }
    
    if(copies==0){
        throw "资金划分份数不能为0，请重新设置";
    }
    
    if(riseRate==0||downRate==0){
       throw "上涨触发和下跌触发百分比不能为0,请重新设置";
    }
}


function get_Command() {
    var cmd = GetCommand(); //获取  交互命令API

    if (cmd != null) {
        arrStr = cmd.split(":");
        if (arrStr[0] == "设置基价") {
            basePrice = arrStr[1];
            Log("设置基价为:", basePrice);
        }  
    }

}



function main() {
    sendEmail("策略启动");
    if (exchanges.length != 1) {
        throw "交易所数量得1个才能启动";
    } else {
        Log("交易所信息:", exchange.GetName(), ":", exchange.GetAccount());
    }

    //检查策略参数
    checkParmers();
 
    //获取上一次策略运行的盈利数据
    var GprofitDif = _G("profitAmount");
    if (GprofitDif != null) {
        profitAmount = GprofitDif;
        Log("【上一次策略运行总获利】" + profitAmount);
    } else {
        //Log("profitDif==null", profitAmount);
    }

    initState = getExchangesState(); //调用自定义的 getExchangesState 函数获取到 所有交易所的信息， 赋值给 initState 

    
    for (var j = 0; j < initState.details.length; j++) {
        account = initState.details[j].account;
        initStateStr += "【" + initState.details[j].exchange.GetName() + "】 " + " 持币：" + account.Stocks + "  冻结币：" + account.FrozenStocks + "  余额:" + account.Balance + "  冻结余额：" + account.FrozenBalance + "\n";
    }

    initStateStr += "【初始状态】总币数：" + initState.allStocks + " 总金额:" + initState.allBalance + "\n"


 
    if (initState.allBalance == 0) {
        throw "所有交易所Balance（余额）数量总和为空";
    }


    //设置线图标题
    $.PlotTitle("价格分析图");


    //手动设置基准价格
    if(!isAutoSetBaseLine){
        initSumTimes=10; //手动设置情况下，大盘观测次数设置为10
    }
    
    while (isWorking) {
        Sleep(parseInt(TickInterval));
        get_Command(); // 获取交互指令
        onTick();
         
    }
    updateStatePrice(getExchangesState()); // 更新价格行情,计算排除手续费影响的对冲价格值

}