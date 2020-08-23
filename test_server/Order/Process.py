from django.shortcuts import HttpResponse
from test_server.Order import addOrder,sendOrders,freightFinality,applyForPayment
from test_server.utils.selectFreight import selectFreight
from test_server.utils.paymentAmount import paymentAmount
from test_server.data.mysqls import Data
import json
class Process():
	def __init__(self):
		pass
	def orderProcess(self,request):
		'''
		：quantity:请求次数
		：status:状态
		：data:创单数据
		:param request:
		:return:
		'''
		self.orderList = []
		self.orderDict = {}
		self.succeed = 0
		self.fail = 0
		print('request:orderProcess')
		if request.method == "POST":
			self.quantity = json.loads(request.body.decode().replace("'", "\"")).get('quantity')
			self.status = json.loads(request.body.decode().replace("'", "\"")).get('status')
			self.orderData = json.loads(request.body.decode().replace("'", "\"")).get('orderData')
			self.driverData = json.loads(request.body.decode().replace("'", "\"")).get('driverData')
			data = Data().query('zyb_test',"SELECT id,bank,number FROM `zyb_pay_bankcard` WHERE bank_authid = {} AND bank_mobile = {} AND del != 1 ORDER BY id DESC LIMIT 1;".format(
									self.driverData['idCard'], self.driverData['driverMobile']))
			if len(data) == 0:
				return HttpResponse(json.dumps({"code": 0, "msg": "司机没有银行卡信息", "data": ""}))

			while self.quantity:
				self.quantity -= 1
				# 调用接单
				self.response = addOrder.Order().addOrder(self.orderData['tmsWLOrder'],self.orderData['wlToken'])
				if self.response['code'] == 1:
					self.succeed += 1
					print(True,self.response['data']['firstOrderId'])
					self.orderList.append(self.response['data']['firstOrderId'])
				else:
					self.fail += 1
					return HttpResponse(json.dumps(self.response))
			print('创单后的list:',self.orderList)
			if self.status > 1:
				# print('sendOrders')
				print('派单的list:', self.orderList)
				for i in self.orderList:
					# 派单
					print('请求派单数据',self.driverData,i,self.orderData['wlToken'])
					sendResponse = sendOrders.sendOrders().sendDriver(i,self.orderData['wlToken'],self.driverData)
					print('派单返回数据：',sendResponse)
					if sendResponse['code'] != 1:
						self.orderList.remove(i)
						return HttpResponse(json.dumps(sendResponse))
			if self.status > 2:
				print('订单查询运单',self.orderList)
				self.freightList = selectFreight(self.orderList)
				print(self.freightList)
				for i in self.freightList:
					response = freightFinality.freightFinality().tmsFinality(self.orderData['wlToken'],i)
					if response['code'] == 0:
						return HttpResponse(json.dumps(response))
			if self.status > 3:
				print('请求paymentAmount参数',self.driverData['subsistMoney'],self.driverData['tailMoney'],self.driverData['backMoney'])
				money = paymentAmount(self.driverData['subsistMoney'],self.driverData['tailMoney'],self.driverData['backMoney'])
				print('款项：',money)
				print(type(money),money)
				if min(money) == 1:
					print(1)
					self.re_money = 'subsistMoney'
				elif min(money) == 2:
					print(2)
					self.re_money = 'tailMoney'
				elif min(money) == 3:
					print(3)
					self.re_money = 'backMoney'
				else:
					print('else')
					return HttpResponse(json.dumps({"code":0,"msg":"没有可支付款项"}))
				for i in self.freightList:
					print('for i in self.freightList:')
					self.requestPayment = {
						"wlToken": self.orderData['wlToken'],
						"type": '{}'.format(min(money)),
						"payObjectSum": "1",
						"freightId": "{}".format(i),
						"payeeName": self.driverData['driverName'],
						"payeeMobile": self.driverData['driverMobile'],
						"payeeId": self.driverData['idCard'],
						"payeeBank": data[0]['bank'],
						"payeeAccount": data[0]['number'],
						"bankcardId": str(data[0]['id']),
						"isEntrust": "0",
						"advancePrice": self.driverData[self.re_money]
					}
					print(self.requestPayment)
					re_data = applyForPayment.applyForPayment().applyForPaymentDriver(self.requestPayment)

					# if re_data['code'] == 0:
					return HttpResponse(json.dumps(re_data))
				money.remove(min(money))
				print(money)
			return HttpResponse(json.dumps({"code":233,"msg":"批量创建:成功{}单"}))
			# return HttpResponse(json.dumps({"code":233,"msg":"批量创建:成功{}单,".format(self.succeed)+"失败{}单,".format(self.fail),"data":"{}".format(self.orderDict)}))

		else:return HttpResponse(json.dumps({"code":0,"msg":"请使用POST请求！","data":""}))


print(Data().query('localhost','SELECT * FROM `my_tb` WHERE id = 1;'))
