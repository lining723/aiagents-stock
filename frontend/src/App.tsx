import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from '@/components/Layout'
import Home from '@/pages/Home'
import ValueStock from '@/pages/stock/ValueStock'
import MainForce from '@/pages/stock/MainForce'
import LonghubangAnalysis from '@/pages/longhubang/Analysis'
import LonghubangHistory from '@/pages/longhubang/History'
import LonghubangStatistics from '@/pages/longhubang/Statistics'
import MonitorConfig from '@/pages/monitor/Config'
import MonitorStocks from '@/pages/monitor/Stocks'
import MonitorNotifications from '@/pages/monitor/Notifications'
import StockAnalysis from '@/pages/analysis/StockAnalysis'
import AnalysisHistory from '@/pages/analysis/History'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhCN}
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: '#1677ff',
          },
        }}
      >
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/stock/value" element={<ValueStock />} />
              <Route path="/stock/main-force" element={<MainForce />} />
              <Route path="/analysis">
                <Route index element={<StockAnalysis />} />
                <Route path="history" element={<AnalysisHistory />} />
              </Route>
              <Route path="/longhubang/analysis" element={<LonghubangAnalysis />} />
              <Route path="/longhubang/history" element={<LonghubangHistory />} />
              <Route path="/longhubang/statistics" element={<LonghubangStatistics />} />
              <Route path="/monitor/config" element={<MonitorConfig />} />
              <Route path="/monitor/stocks" element={<MonitorStocks />} />
              <Route path="/monitor/notifications" element={<MonitorNotifications />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  )
}

export default App
