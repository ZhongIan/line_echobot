import numpy as np
import pandas as pd

class VaR:
    # @staticmethod 裝飾器 無須實例化即可調用
    

    @staticmethod
    def download_from_yahoo(name, year=2015):
        '''
        抓取YAHOO的資料
        含需回測風險值的年份，以及前兩年(計算所需)，
        共3年

        input:
            name: 股票名稱
            year:需回測風險值的年份

        output:
            data: ['Adj Close','return']共3年
            data_Forecast: ['Adj Close','return'] year當年
            num_For: year當年資料長度
            num_his: 前兩年(計算所需)的資料長度
        '''

        from datetime import datetime 
        # pandas web 爬雅虎的修正
        import fix_yahoo_finance as yf
        # 測試
        yf.pdr_override()

        start = datetime(year-2,1,1) # 開始日期
        end = datetime(year,12,31) # 結束日期

        df = yf.download([name+'.TW'], start, end)
        df=df.loc[df['Volume']>0] # yahoo的資料有些錯誤(如:國定假日)
        df['return'] = df['Adj Close'].pct_change()
        data = df.loc[:,['Adj Close','return']]
        data_Forecast = data[data.index.year == 2015]

        num_For = data_Forecast.shape[0]
        num_his = data.shape[0] - num_For
    
        return(data, data_Forecast, num_For, num_his)
    
    
    @staticmethod
    def hist_method(data, data_Forecast, num_his, alpha):
        '''
        歷史模擬法

        input:
            data: ['Close','return']共3年
            data_Forecast: ['Close','return'] 預測期當年
            num_his: 前兩年(計算所需)的資料長度
            alpha: alpha值 [0.01,0.05]

        output:
            data_hist: 風險值資料(歷史模擬法)
            dis_VaR: VaR穿透數
            dis_CVaR: CVaR穿透數
        '''

        # num:排序序位 ; 由於排序函數(sort_num,sort_num_sum)，
        # 的序位均由 0 開始，因此 -1
        num = int((num_his-1)*alpha) - 1
        # 避免干擾源資料
        data_hist = data_Forecast[:]

        # @ 排序函數
        def sort_num(arr, num):
            '''
            對數組(arr)排序直到,序位{num}(0...num) 
            '''
            r = arr[np.argpartition(arr, num)[num]]
            return r

        def sort_num_sum(arr, num):
            '''
            對數組(arr)排序直到,序位{num},並選取{[:num+1]]}(0...num),作加總
            '''
            r = arr[np.argpartition(arr, num)[:num+1]].sum() 
            return  r

        # 風險值計算
        # rolling: 移動視窗，用過去資料，評斷未來，大小為 num_his(0...num_his-1)
        data_hist['VaR'] = data.loc[:,['return']].rolling(num_his-1).apply(
            lambda arr: sort_num(arr, num),
            # raw=True 向函數(lambda)傳送 ndarray
            raw=True
        # shift(1): 數據向後移一天 # dropna():去除 nan
        ).shift(1).dropna()

        # 條件風險值計算
        data_hist['CVaR'] =  data.loc[:,['return']].rolling(num_his-1).apply(
            # ex:序位2(0.1.2)，實際總數為 3，故 +1
            lambda arr: sort_num_sum(arr, num)/(num+1),
            raw=True
        ).shift(1).dropna()

        data_hist = data_hist.loc[:,['return','VaR','CVaR']]
        # VaR穿透數
        dis_VaR = data_hist[data_hist['return'] < data_hist['VaR']].shape[0]
        # CVaR穿透數
        dis_CVaR = data_hist[data_hist['return'] < data_hist['CVaR']].shape[0]

        return(data_hist, dis_VaR, dis_CVaR)
    
    
    @staticmethod
    def sigma_method(data, num_his, method='sample'):
        '''
        變異數(sigma)的估算

        input:
            data: ['Close','return']共3年
            num_his: 前兩年(計算所需)的資料長度
            method: 分為'sample'(簡單)，'weighted'(指數)

        output:
            sigma: method == 'sample' -> sample_sigma
                    method == 'weighted' -> weighted_sigma

        '''

        # 變異數(簡單)
        if method == 'sample':
            sample_sigma = data.loc[:,['return']].rolling(num_his-1).apply(
                lambda arr: np.std(arr), 
                raw=True
            ).shift(1).dropna()

            return sample_sigma
        # 變異數(指數)
        elif method == 'weighted':
            # 需用前一筆變異數(簡單)，故 num_his-2
            sample_sigma = data.loc[:,['return']].rolling(num_his-2).apply(
                lambda arr: np.std(arr), 
                raw=True
            )
            # 加權移動平均(指數)
            weighted_sigma = (
                0.94*sample_sigma.shift(1)**2 + (1-0.94)*data.loc[:,['return']].iloc[num_his-1:,:]**2
            )**0.5

            return weighted_sigma.shift(1).dropna()
        
        
    @staticmethod
    def cm_method(data, data_Forecast, num_his, method='sample', alpha=0.05):
        '''
        變異數_共變異數法

        input:
            data: ['Close','return']共3年
            data_Forecast: ['Close','return'] 預測期當年
            num_his: 前兩年(計算所需)的資料長度
            method: 調用sigma_method函數，'sample' OR 'weighted'
            alpha: alpha值 [0.01,0.05]

        output:
            data_cm: 風險值資料(變異數_共變異數法)
            dis_VaR: VaR穿透數
            dis_CVaR: CVaR穿透數
        '''

        if alpha == 0.05:
            z=1.645
        elif alpha == 0.01:
            z=2.33

        data_cm = data_Forecast[:]

        sigma = VaR.sigma_method(data, num_his, method=method)

        data_cm['VaR'] = -z*sigma*1
        data_cm['CVaR'] = (1/alpha)*-(sigma/((2*np.pi)**0.5))*np.exp(-((-z*sigma*1)**2)/(2*(sigma**2)))

        dis_VaR = data_cm[data_cm['return'] < data_cm['VaR']].shape[0]
        dis_CVaR = data_cm[data_cm['return'] < data_cm['CVaR']].shape[0]

        data_cm = data_cm.loc[:,['return','VaR','CVaR']]

        return(data_cm, dis_VaR, dis_CVaR)
    
    
    @staticmethod
    def mote_method(data, data_Forecast, num_his, method='sample', alpha=0.05):
        '''
        蒙地卡羅法

        input:
            data: ['Close','return']共3年
            data_Forecast: ['Close','return'] 預測期當年
            num_his: 前兩年(計算所需)的資料長度
            method: 調用sigma_method函數，'sample' OR 'weighted'
            alpha: alpha值 [0.01,0.05]

        output:
            data_mote: 風險值資料(蒙地卡羅法)
            dis_VaR: VaR穿透數
            dis_CVaR: CVaR穿透數

        '''

        t = 10 # 分成t期
        N = 1000 # N條不同路徑(隨機數)

        data_mote = data_Forecast[:]

        sigma = VaR.sigma_method(data, num_his , method=method)['return'].values
        # 股價平均數
        u = data['return'].rolling(num_his-1).mean().shift(1).dropna().values
        # 隨機數
        er = np.random.randn(N,t,len(u))
        # N條不同隨機數的 return
        mt_var_N = ((u-(sigma**2)/2)*(1/t)+sigma*((1/t)**0.5)*er).sum(axis=1)

        axis = 0
        sort_num = int(N*alpha) - 1
        # 另一軸
        another_axis = np.arange(mt_var_N.shape[1])[None,:]
        # 排序序位情形
        sort_status = np.argpartition(mt_var_N, sort_num, axis=axis)
        top = sort_status[sort_num, :]
        # [:sort_num+1, :]，對 axis=0 取到 num(0...num)
        top_for_sum = sort_status[:sort_num+1, :]

        data_mote['VaR'] = mt_var_N[top,another_axis].ravel()
        data_mote['CVaR'] = (
            mt_var_N[top_for_sum,another_axis].sum(axis=axis)/(sort_num+1)
        ).ravel()

        data_mote = data_mote.loc[:,['return','VaR','CVaR']]

        dis_VaR = data_mote[data_mote['return'] < data_mote['VaR']].shape[0]
        dis_CVaR = data_mote[data_mote['return'] < data_mote['CVaR']].shape[0]

        return(data_mote, dis_VaR, dis_CVaR)
    
    
       
    def output(self, func):
        (data_result, dis_VaR, dis_CVaR) = func
        data_result.plot()
        dis = round(self.num_For*self.alpha,2)
        """ print(
            f'理論穿透:{dis}\n' + \
            f'VaR穿透數:{dis_VaR}\nCVaR穿透數:{dis_CVaR}'
        ) """

        return(data_result, dis_VaR, dis_CVaR)
        
    
    def __init__(self, name='2330', year=2015, alpha=0.05, method='sample'):
        (self.data, self.data_Forecast, self.num_For, self.num_his) = self.download_from_yahoo(name, year)
        self.alpha = alpha
        self.method = 'sample' # for sigma_method: 'sample'(簡單)，'weighted'(指數)
        
        # 各個方法的函數
        self.method_func_dict = {
            '歷史模擬法':self.hist_method,
            '變異數_共變異數法':self.cm_method,
            '蒙地卡羅法':self.mote_method
        }
        # 各個方法的函數所需的參數
        self.method_agrs_dict = {
            '歷史模擬法':{
                'data': self.data,
                'data_Forecast': self.data_Forecast,
                'num_his': self.num_his, 
                'alpha': self.alpha
            },
            '變異數_共變異數法':{
                'data': self.data,
                'data_Forecast': self.data_Forecast,
                'num_his': self.num_his,
                'method':self.method,
                'alpha': self.alpha
            },
            '蒙地卡羅法':{
                'data': self.data,
                'data_Forecast': self.data_Forecast,
                'num_his': self.num_his,
                'method':self.method,
                'alpha': self.alpha
            }
        }
        
        
        
    def main(self, method_name='歷史模擬法'):
        (data_result, dis_VaR, dis_CVaR) = self.output(
            func= self.method_func_dict[method_name](
                **self.method_agrs_dict[method_name]
            )
        )

        return(data_result, dis_VaR, dis_CVaR)
        
if __name__=='__main__':
    a = VaR(name='2330', year=2015, alpha=0.05, method='sample')
    a.main(method_name='歷史模擬法')