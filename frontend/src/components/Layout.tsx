import { ReactNode } from 'react'
import { Layout as AntLayout, Typography, Menu } from 'antd'
import { Link, useLocation } from 'react-router-dom'
import {
  HomeOutlined,
  StockOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

const { Header, Content, Sider } = AntLayout
const { Title } = Typography

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: 'stock',
      icon: <StockOutlined />,
      label: '选股模块',
      children: [
        {
          key: '/stock/value',
          label: <Link to="/stock/value">低估值策略</Link>,
        },
        {
          key: '/stock/main-force',
          label: <Link to="/stock/main-force">主力选股</Link>,
        },
      ],
    },
    {
      key: 'analysis',
      icon: <BarChartOutlined />,
      label: '股票分析',
      children: [
        {
          key: '/analysis',
          label: <Link to="/analysis">新建分析</Link>,
        },
        {
          key: '/analysis/history',
          label: <Link to="/analysis/history">分析历史</Link>,
        },
      ],
    },
    {
      key: 'longhubang',
      icon: <TrophyOutlined />,
      label: '智瞰龙虎',
      children: [
        {
          key: '/longhubang/analysis',
          label: <Link to="/longhubang/analysis">龙虎榜分析</Link>,
        },
        {
          key: '/longhubang/history',
          label: <Link to="/longhubang/history">历史报告</Link>,
        },
        {
          key: '/longhubang/statistics',
          label: <Link to="/longhubang/statistics">数据统计</Link>,
        },
      ],
    },
    {
      key: 'monitor',
      icon: <ClockCircleOutlined />,
      label: '智能盯盘',
      children: [
        {
          key: '/monitor/config',
          label: <Link to="/monitor/config">盯盘配置</Link>,
        },
        {
          key: '/monitor/stocks',
          label: <Link to="/monitor/stocks">监测股票</Link>,
        },
        {
          key: '/monitor/notifications',
          label: <Link to="/monitor/notifications">提醒通知</Link>,
        },
      ],
    },
  ]

  const selectedKeys = [location.pathname]
  const openKeys = location.pathname.startsWith('/stock')
    ? ['stock']
    : location.pathname.startsWith('/longhubang')
    ? ['longhubang']
    : location.pathname.startsWith('/monitor')
    ? ['monitor']
    : []

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <Title level={3} style={{ color: 'white', margin: 0 }}>
          📈 AI Agents Stock
        </Title>
      </Header>
      <AntLayout>
        <Sider width={250} style={{ background: '#f0f2f5' }}>
          <Menu
            mode="inline"
            selectedKeys={selectedKeys}
            defaultOpenKeys={openKeys}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>
        <AntLayout style={{ padding: '24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: 'white',
              borderRadius: '8px',
            }}
          >
            {children}
          </Content>
        </AntLayout>
      </AntLayout>
    </AntLayout>
  )
}
