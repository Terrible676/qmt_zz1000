#encoding:gbk
'''
中证1000Mini_1234/(High-Low+0.02)
'''
import pandas as pd
import numpy as np
import talib
import copy
# import numba
def init(ContextInfo):
	ContextInfo.accID = '818052180'
	#ContextInfo.buy = True
	#ContextInfo.sell = False
	ContextInfo.count = 0
	ContextInfo.capital = 900000
	ContextInfo.lastpos = pd.Series()
	ContextInfo.MaxPos = 0.95
	ContextInfo.set_account('818052180')
	#ContextInfo.benchmark
def after_init(ContextInfo):
	pass
	
def handlebar(ContextInfo):
	'''
	每日230分时运行一次
	if(ContextInfo.count != 230):
		return
	'''
	# 查询账户持仓
	position_info = get_trade_detail_data(ContextInfo.accID, 'stock', 'position')
	print('')
	print('position_info:',len(position_info))
	print('')
	print('实盘账户持仓：',end=' ')
	
	for i in position_info:
		print(i.m_strInstrumentID, i.m_nVolume,end=' ')
	#可用资金查询
	acct_info = get_trade_detail_data(ContextInfo.accID, 'stock', 'account')
	for i in acct_info:
		print(i.m_dAvailable)


	#accountData = get_trade_detail_data('818052180', 'stock', 'position')
	#print('accountData:',accountData)
	
	now = get_market_time('SH')
	if(ContextInfo.count==0):
		print('now:',now)
	StockList = ContextInfo.get_stock_list_in_sector('中证1000')
	'''
	st = get_st_status(StockList[0])
	print('st:',st)
	'''
	print('Barpos:',ContextInfo.barpos,end=' ')
	
	ContextInfo.set_universe(StockList)
	'''
	exStock1 = ContextInfo.get_his_contract_list('SH')
	print('exStock1:',exStock1)
	exStock2 = ContextInfo.get_his_contract_list('SZ')
	print('exStock2:',exStock2)
	'''
	ContextInfo.count += 1
	if(ContextInfo.count==1):
		print(StockList[0:5])
		print('Totoal Stocks: ',len(StockList))
	
	
	#CloseData = ContextInfo.get_history_data(60,'1d','close',dividend_type=1)
	#HighData = ContextInfo.get_history_data(1,'1d','high',dividend_type=1)
	#LowData = ContextInfo.get_history_data(1,'1d','low',dividend_type=1)
	#AmountData = ContextInfo.get_history_data(1,'1d','',dividend_type=1)
	
	df = ContextInfo.get_market_data(['close', 'high','low','amount'], 
		stock_code = StockList, skip_paused = True, 
		period = '1d', dividend_type = 'front', count = 60)
	if(ContextInfo.count==1):
		print(df)
		print(type(df))
	
	#cp = df.loc['close'][0]
	'''
	stock = '000918.SZ'
	cp = df.loc[stock]['close']
	if(ContextInfo.count==1):
		print('cp:')
		print(cp[0:5])
		print('type cp:',type(cp))
	'''
	
	# ContextInfo.lastpos = pd.Series(index=StockList, data=0)
	alphaMat = pd.Series(index=StockList, data=0)
	'''
	if(ContextInfo.count==1):
		print(alphaMat)
	'''
	i=0
	for stock in StockList:
		i += 1
		try:
			#tmpPrice = CloseData[stock]
			tmpPrice = df.loc[stock]['close']
			tmpLow = df.loc[stock]['low']
			tmpHigh = df.loc[stock]['high']
			tmpAmount = df.loc[stock]['amount']
		except:
			print('No Stock Data',end=' ')
			continue
		'''
		if(ContextInfo.count==1 and i==1):
			print(stock,':',tmpPrice)
			print(type(tmpPrice))
		'''
		ReToHigh =(1- tmpPrice[-1]/max(tmpPrice))*100
		if(ContextInfo.count==1 and i==1):
			print('ReToHigh:',ReToHigh)
		ReToLow =(tmpPrice[-1]/min(tmpPrice)-1)*100
		if(ContextInfo.count==1 and i==1):
			print('ReToLow:',ReToLow)
		
		try:
			con1 = (ReToHigh<20 and ReToLow>5 and ReToLow<15)## 1mark
			con2 = (ReToHigh>20 and ReToLow>5)## 3mark
			con3 = (tmpAmount[-1]<50000000 and tmpAmount[-1]>10000000)
			con4 = (tmpPrice[-1]>5)
			con5 = (ReToHigh > 5 and ReToHigh <15)
			#con6 = (ReToHigh > 20 and ReToLow < 5)
			if(ContextInfo.count==1 and i==10):
				print(stock)
				print(tmpAmount[-1])
				print(con1,con2,con3,con4)
			
			factor1 =  1/(tmpHigh[-1] - tmpLow[-1] +0.02)
			alphaMat.loc[stock] = factor1 * int((con1 or con2) and con3 and con4 and (not con5))
			
			#alpha *= (Amount<50000000) * (ClosePrice>5) *(Amount>10000000)
		except:
			continue
	#if(ContextInfo.count==10):
	
	alphaMat.fillna(0)
	alphaMat = alphaMat[alphaMat>0]
	print(ContextInfo.count,' alpha:',alphaMat.sum())
	alphaMat = alphaMat* (ContextInfo.capital/alphaMat.sum())*ContextInfo.MaxPos  # 计算每个股票的持仓金额
	print('ContextInfo.capital:',ContextInfo.capital)
	for stock in alphaMat.index:
		try:
			tmpPrice = df.loc[stock]['close']
		except:
			print('No Stock Data',end=' ')
			continue
		alphaMat.loc[stock] = int(alphaMat.loc[stock]/(100*tmpPrice[-1]))
	# print(alphaMat)
	'''
	position_info = get_trade_detail_data('818052180', 'stock', 'position')
	if(ContextInfo.count==3):
		print('position_info:')
		for i in position_info:
			print(i.m_strInstrumentID, i.m_nVolume)
	'''
	
	# Trade
	if(len(ContextInfo.lastpos)==0):
		ContextInfo.lastpos =copy.deepcopy(0*alphaMat)
	alphaCon = pd.concat([ContextInfo.lastpos, alphaMat], axis=1)
	alphaCon = alphaCon.fillna(0)
	print('')
	# print(alphaCon)
	alphaDelta = (alphaCon[1]-alphaCon[0]).astype(int) 
	alphaDelta = alphaDelta[alphaDelta!=0]
	ContextInfo.lastpos = copy.deepcopy(alphaMat)
	# print(alphaDelta)
	#for stock in alphaCon.index:
		
		#order_lots(stock,alphaMat.loc[stock],ContextInfo,ContextInfo.accID) # 手数
	
	# 先卖再买
	'''
	# 实盘跳过历史信号
	if not ContextInfo.is_last_bar():
	#历史k线不应该发出实盘信号 跳过
		return
	'''

	#if ContextInfo.is_last_bar():
	for stock in alphaDelta.index:
		try:
			if(alphaDelta[stock]<0):
				order_lots(stock,int(alphaDelta[stock]),'MARKET',ContextInfo,'808052180')#ContextInfo.accID
				
							# 用14.00元限价买入股票s 100股
				#passorder(23,1101,account,s,11,14.00,100,1,ContextInfo)  # 当前k线为最新k线 则立即下单
				#passorder(23,1101,account,s,5,-1,100,0,ContextInfo)  # K线走完下单
				# 用最新价限价买入股票s 1000元
				#passorder(23, 1102, account, s, 5, 0,1000, 2, ContextInfo)  # 不管是不是最新K线，立即下单

				print('sold ',stock,' ',int(alphaDelta[stock]),end=' ')
		except:
			print('Order Failed.', end= '')
			continue
	
	for stock in alphaDelta.index:
		try:
			if(alphaDelta[stock]>0):
				order_lots(stock,int(alphaDelta[stock]),'MARKET',ContextInfo,'808052180')#ContextInfo.accID
				print('bought ',stock,' ',int(alphaDelta[stock]),end=' ')
		except:
			print('Order Failed.', end=' ')
			continue

# 仅实盘状态下生效，需在init中调用ContextInfo.set_account

# 资金账号状态变化主推 account_callback()
'''
def account_callback(ContextInfo, accountInfo):
	global A
	A.account['Balance'] = accountInfo.m_dBalance
	A.account['Available'] = accountInfo.m_dAvailable
	A.account['InstrumentValue'] = accountInfo.m_dInstrumentValue
'''
# 账号任务状态变化主推 task_callback()
def order_callback(ContextInfo, orderInfo):
	print('orderInfo')

# 账号委托状态变化主推 order_callback()
def task_callback(ContextInfo, taskInfo):
	print('taskInfo')

# 账号成交状态变化主推 deal_callback()
def deal_callback(ContextInfo, dealInfo):
	print('dealInfo')

# 账号持仓状态变化主推 position_callback()
def position_callback(ContextInfo, positonInfo):
	print('positonInfo')

# 账号异常下单主推 orderError_callback()
def position_callback(ContextInfo,orderArgs,errMsg):
	print('orderArgs')
	print(errMsg)



'''
本示例用于演示如何通过函数获取指定账户的委托、持仓、资金数据

#coding:gbk


def to_dict(obj):
	attr_dict = {}
	for attr in dir(obj):
		try:
			if attr[:2] == 'm_':
				attr_dict[attr] = getattr(obj, attr)
		except:
			pass
	return attr_dict


def init(C):
	pass
	#orders, deals, positions, accounts = query_info(C)


def handlebar(C):
	if not C.is_last_bar():
		return
	orders, deals, positions, accounts = query_info(C)


def query_info(C):
	orders = get_trade_detail_data('8000000213', 'stock', 'order')
	for o in orders:
		print(f'股票代码: {o.m_strInstrumentID}, 市场类型: {o.m_strExchangeID}, 证券名称: {o.m_strInstrumentName}, 买卖方向: {o.m_nOffsetFlag}',
		f'委托数量: {o.m_nVolumeTotalOriginal}, 成交均价: {o.m_dTradedPrice}, 成交数量: {o.m_nVolumeTraded}, 成交金额:{o.m_dTradeAmount}')


	deals = get_trade_detail_data('8000000213', 'stock', 'deal')
	for dt in deals:
		print(f'股票代码: {dt.m_strInstrumentID}, 市场类型: {dt.m_strExchangeID}, 证券名称: {dt.m_strInstrumentName}, 买卖方向: {dt.m_nOffsetFlag}', 
		f'成交价格: {dt.m_dPrice}, 成交数量: {dt.m_nVolume}, 成交金额: {dt.m_dTradeAmount}')

	positions = get_trade_detail_data('8000000213', 'stock', 'position')
	for dt in positions:
		print(f'股票代码: {dt.m_strInstrumentID}, 市场类型: {dt.m_strExchangeID}, 证券名称: {dt.m_strInstrumentName}, 持仓量: {dt.m_nVolume}, 可用数量: {dt.m_nCanUseVolume}',
		f'成本价: {dt.m_dOpenPrice:.2f}, 市值: {dt.m_dInstrumentValue:.2f}, 持仓成本: {dt.m_dPositionCost:.2f}, 盈亏: {dt.m_dPositionProfit:.2f}')


	accounts = get_trade_detail_data('8000000213', 'stock', 'account')
	for dt in accounts:
		print(f'总资产: {dt.m_dBalance:.2f}, 净资产: {dt.m_dAssureAsset:.2f}, 总市值: {dt.m_dInstrumentValue:.2f}', 
		f'总负债: {dt.m_dTotalDebit:.2f}, 可用金额: {dt.m_dAvailable:.2f}, 盈亏: {dt.m_dPositionProfit:.2f}')

	return orders, deals, positions, accounts
'''
