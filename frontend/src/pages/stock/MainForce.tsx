import { useState } from 'react'
import {
  Card,
  Typography,
  Button,
  Slider,
  Table,
  Alert,
  Space,
  InputNumber,
  Row,
  Col,
  Tag,
  Spin,
  Modal,
} from 'antd'
import { ThunderboltOutlined, RobotOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { stockApi } from '@/services/stockApi'
import type { MainForceStockRequest } from '@/types/stock'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography

export default function MainForceStock() {
  const navigate = useNavigate()
  const [params, setParams] = useState<MainForceStockRequest>({
    days_ago: 5,
    min_market_cap: 10,
    max_market_cap: 500,
    max_range_change: 20,
    top_n: 10,
  })

  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])

  const mutation = useMutation({
    mutationFn: stockApi.getMainForceStocks,
  })

  const handleSearch = () => {
    setSelectedRowKeys([])
    mutation.mutate(params)
  }

  const batchAiMutation = useMutation({
    mutationFn: stockApi.getBatchAIAnalysis,
    onSuccess: (data) => {
      Modal.success({
        title: '批量分析完成',
        content: `成功分析 ${data.success_count} 只股票，失败 ${data.failed_count} 只。分析报告已保存到历史记录中。`,
        okText: '去查看',
        onOk: () => {
          navigate('/analysis/history')
        }
      })
      setSelectedRowKeys([])
    },
    onError: (error) => {
      message.error('批量分析失败: ' + error.message)
    }
  })

  const handleBatchAnalysis = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要分析的股票')
      return
    }
    
    const selectedSymbols = selectedRowKeys.map(key => {
      const stock = mutation.data?.stocks.find(s => s.symbol === key)
      return stock?.symbol || key.toString()
    })
    
    Modal.confirm({
      title: '批量AI深度分析',
      content: `确定要对选中的 ${selectedSymbols.length} 只股票进行AI深度分析吗？这可能需要几分钟时间。`,
      onOk: () => {
        batchAiMutation.mutate({ symbols: selectedSymbols, days_ago: 60 })
      }
    })
  }

  const formatMarketCap = (val?: number) => {
    if (!val) return '-'
    if (val >= 100000000) {
      return `${(val / 100000000).toFixed(2)}亿`
    }
    return `${(val / 10000).toFixed(2)}万`
  }

  const formatMoney = (val?: number) => {
    if (!val) return '-'
    if (val >= 100000000) {
      return `${(val / 100000000).toFixed(2)}亿`
    }
    return `${(val / 10000).toFixed(2)}万`
  }

  const formatPercent = (val?: number) => {
    if (val === undefined || val === null) return '-'
    const sign = val >= 0 ? '+' : ''
    return `${sign}${val.toFixed(2)}%`
  }

  const formatFundFlow = (val?: number) => {
    if (val === undefined || val === null) return '-'
    const color = val >= 0 ? '#52c41a' : '#ff4d4f'
    return (
      <Text style={{ color }}>
        {val >= 0 ? '+' : ''}{val.toFixed(2)}万
      </Text>
    )
  }

  const getRangeChangeTag = (val?: number) => {
    if (val === undefined || val === null) return <Tag>-</Tag>
    const color = val >= 0 ? 'green' : 'red'
    return <Tag color={color}>{formatPercent(val)}</Tag>
  }

  const columns = [
    {
      title: '序号',
      key: 'index',
      width: 60,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
    },
    {
      title: '股票名称',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '市盈率',
      dataIndex: 'pe_ratio',
      key: 'pe_ratio',
      width: 80,
      render: (val: number) => val?.toFixed?.(2) || '-',
    },
    {
      title: '市净率',
      dataIndex: 'pb_ratio',
      key: 'pb_ratio',
      width: 80,
      render: (val: number) => val?.toFixed?.(2) || '-',
    },
    {
      title: '市值',
      dataIndex: 'market_cap',
      key: 'market_cap',
      width: 100,
      render: formatMarketCap,
    },
    {
      title: '涨跌幅',
      dataIndex: 'range_change',
      key: 'range_change',
      width: 100,
      render: getRangeChangeTag,
    },
    {
      title: '主力资金净流入',
      dataIndex: 'main_fund_inflow',
      key: 'main_fund_inflow',
      width: 140,
      render: formatFundFlow,
    },
    {
      title: '所属行业',
      dataIndex: 'industry',
      key: 'industry',
      width: 150,
    },
  ]

  const stocks = mutation.data?.stocks || []

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={2}><ThunderboltOutlined /> 主力选股</Title>
        <Paragraph>
          基于主力资金流向、涨跌幅、市值等多维度筛选 — 捕捉主力介入的潜力标的
        </Paragraph>
      </Card>

      <Card title="参数设置">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col span={8}>
              <Paragraph>数据天数：{params.days_ago}</Paragraph>
              <Slider
                min={1}
                max={30}
                value={params.days_ago}
                onChange={(val) => setParams({ ...params, days_ago: val })}
              />
            </Col>
            <Col span={8}>
              <Paragraph>最小市值(亿)</Paragraph>
              <InputNumber
                min={1}
                max={10000}
                value={params.min_market_cap}
                onChange={(val) => setParams({ ...params, min_market_cap: val || 10 })}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={8}>
              <Paragraph>最大市值(亿)</Paragraph>
              <InputNumber
                min={1}
                max={10000}
                value={params.max_market_cap}
                onChange={(val) => setParams({ ...params, max_market_cap: val || 500 })}
                style={{ width: '100%' }}
              />
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Paragraph>最大涨跌幅(%)：{params.max_range_change}</Paragraph>
              <Slider
                min={5}
                max={50}
                value={params.max_range_change}
                onChange={(val) => setParams({ ...params, max_range_change: val })}
              />
            </Col>
            <Col span={12}>
              <Paragraph>返回前 N 只：{params.top_n}</Paragraph>
              <Slider
                min={5}
                max={50}
                value={params.top_n}
                onChange={(val) => setParams({ ...params, top_n: val })}
              />
            </Col>
          </Row>
          <Button
            type="primary"
            onClick={handleSearch}
            loading={mutation.isPending}
            size="large"
          >
            开始选股
          </Button>
        </Space>
      </Card>

      {mutation.isError && (
        <Alert
          message="选股失败"
          description={(mutation.error as Error)?.message || '请稍后重试'}
          type="error"
          showIcon
        />
      )}

      {mutation.isSuccess && (
        <Card 
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>选股结果 ({stocks.length} 只)</span>
              <Button 
                type="primary" 
                icon={<RobotOutlined />} 
                onClick={handleBatchAnalysis}
                disabled={selectedRowKeys.length === 0}
                loading={batchAiMutation.isPending}
              >
                批量 AI 深度分析 ({selectedRowKeys.length})
              </Button>
            </div>
          }
        >
          {mutation.data?.message && (
            <Alert
              message={mutation.data.message}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          <Spin spinning={mutation.isPending}>
            <Table
              rowSelection={{
                selectedRowKeys,
                onChange: (newSelectedRowKeys) => setSelectedRowKeys(newSelectedRowKeys),
              }}
              dataSource={stocks}
              columns={columns}
              rowKey="symbol"
              pagination={{ pageSize: 10 }}
              scroll={{ x: 1200 }}
            />
          </Spin>
        </Card>
      )}
    </Space>
  )
}
