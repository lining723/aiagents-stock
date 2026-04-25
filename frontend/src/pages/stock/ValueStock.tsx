import { useState } from 'react'
import {
  Card,
  Typography,
  Button,
  Slider,
  Table,
  Alert,
  Space,
  Row,
  Col,
  Tag,
  Spin,
  Modal,
  message,
} from 'antd'
import { ExperimentOutlined, RobotOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { stockApi } from '@/services/stockApi'
import type { ValueStockRequest } from '@/types/stock'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph } = Typography

export default function ValueStock() {
  const navigate = useNavigate()
  const [params, setParams] = useState<ValueStockRequest>({
    top_n: 10,
    pe_max: 20.0,
    pb_max: 1.5
  })

  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])

  const mutation = useMutation({
    mutationFn: stockApi.getValueStocks,
  })

  const handleSelect = () => {
    setSelectedRowKeys([])
    mutation.mutate(params)
  }

  const batchAiMutation = useMutation({
    mutationFn: stockApi.getBatchAIAnalysis,
    onSuccess: (data) => {
      Modal.success({
        title: '批量分析完成',
        content: `成功分析 ${data?.success_count ?? 0} 只股票，失败 ${data?.failed_count ?? 0} 只。分析报告已保存到历史记录中。`,
        okText: '去查看',
        onOk: () => {
          navigate('/analysis/history')
        },
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
    
    // 提取选中的股票代码（去掉市场后缀，如 .SH, .SZ，如果有的话。或者根据后端需要调整）
    // 当前接口 symbol 需要单纯的数字代码或带后缀均可，但建议保持和表格数据一致
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

  const formatPercent = (val?: number) => {
    if (val === undefined || val === null) return '-'
    return `${val.toFixed(2)}%`
  }

  const getValueTag = (pe?: number, pb?: number) => {
    if (pe === undefined || pb === undefined) return <Tag>-</Tag>
    const peMax = params.pe_max ?? 20
    const pbMax = params.pb_max ?? 1.5
    const isValue = pe <= peMax && pb <= pbMax
    return <Tag color={isValue ? 'green' : 'orange'}>{isValue ? '低估值' : '关注'}</Tag>
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
      title: '估值标签',
      key: 'value_tag',
      width: 100,
      render: (_: any, record: any) => getValueTag(record.pe_ratio, record.pb_ratio),
    },
    {
      title: '市盈率',
      dataIndex: 'pe_ratio',
      key: 'pe_ratio',
      width: 90,
      render: (val: number) => val?.toFixed?.(2) || '-',
    },
    {
      title: '市净率',
      dataIndex: 'pb_ratio',
      key: 'pb_ratio',
      width: 90,
      render: (val: number) => val?.toFixed?.(2) || '-',
    },
    {
      title: '股息率',
      dataIndex: 'dividend_rate',
      key: 'dividend_rate',
      width: 90,
      render: formatPercent,
    },
    {
      title: '资产负债率',
      dataIndex: 'debt_ratio',
      key: 'debt_ratio',
      width: 100,
      render: formatPercent,
    },
    {
      title: '市值',
      dataIndex: 'market_cap',
      key: 'market_cap',
      width: 100,
      render: formatMarketCap,
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
        <Title level={2}><ExperimentOutlined /> 低估值策略</Title>
        <Paragraph>
          低PE + 低PB + 高股息 + 低负债 — 寻找被市场低估的优质标的
        </Paragraph>
      </Card>

      <Card title="参数设置">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Paragraph>选股策略说明：</Paragraph>
              <ul style={{ marginLeft: 16, color: '#666' }}>
                <li>市盈率 ≤ {params.pe_max}</li>
                <li>市净率 ≤ {params.pb_max}</li>
                <li>股息率 ≥ 1%</li>
                <li>资产负债率 ≤ 30%</li>
                <li>非ST、非科创板、非创业板</li>
                <li>按流通市值由小到大排名</li>
              </ul>
            </Col>
            <Col span={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Paragraph>最大市盈率 (PE)：{params.pe_max}</Paragraph>
                  <Slider
                    min={5}
                    max={50}
                    value={params.pe_max}
                    onChange={(val) => setParams({ ...params, pe_max: val })}
                  />
                </div>
                <div>
                  <Paragraph>最大市净率 (PB)：{params.pb_max}</Paragraph>
                  <Slider
                    min={0.5}
                    max={5.0}
                    step={0.1}
                    value={params.pb_max}
                    onChange={(val) => setParams({ ...params, pb_max: val })}
                  />
                </div>
                <div>
                  <Paragraph>返回前 N 只：{params.top_n}</Paragraph>
                  <Slider
                    min={5}
                    max={50}
                    value={params.top_n}
                    onChange={(val) => setParams({ ...params, top_n: val })}
                  />
                </div>
              </Space>
            </Col>
          </Row>
          <Button
            type="primary"
            onClick={handleSelect}
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
          title={`选股结果 (${stocks.length} 只)`}
          extra={
            <Button 
              type="primary" 
              icon={<RobotOutlined />} 
              onClick={handleBatchAnalysis}
              disabled={selectedRowKeys.length === 0}
              loading={batchAiMutation.isPending}
            >
              批量 AI 深度分析 ({selectedRowKeys.length})
            </Button>
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
