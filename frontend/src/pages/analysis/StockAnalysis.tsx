import { useState } from 'react'
import {
  Card,
  Typography,
  Button,
  Input,
  Tabs,
  Table,
  Alert,
  Space,
  Row,
  Col,
  Tag,
  Spin,
  Progress,
  Statistic,
  Divider,
  List,
  Checkbox,
} from 'antd'
import type { TabsProps } from 'antd'
import { BarChartOutlined, LineChartOutlined, FundOutlined, RobotOutlined, SlidersOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import KlineChart from '@/components/KlineChart'
import { stockApi } from '@/services/stockApi'
import type {
  ComprehensiveAnalysisRequest,
  ComprehensiveAnalysisResponse,
  AnalysisDimension,
  TechnicalAnalysisResponse,
  FundamentalAnalysisResponse,
  PricePredictionResponse,
  AIAnalysisRequest,
} from '@/types/stock'

const { Title, Paragraph, Text } = Typography

export default function StockAnalysis() {
  const [symbol, setSymbol] = useState<string>('000001')
  const [daysAgo, setDaysAgo] = useState<number>(60)
  const [analysisDimensions, setAnalysisDimensions] = useState<AnalysisDimension[]>([
    'technical',
    'fundamental',
    'price_prediction',
  ])
  const [enableAIAnalysis, setEnableAIAnalysis] = useState<boolean>(true)

  const mutation = useMutation({
    mutationFn: (request: ComprehensiveAnalysisRequest) =>
      stockApi.getComprehensiveAnalysis(request),
  })

  const aiMutation = useMutation({
    mutationFn: (request: AIAnalysisRequest) =>
      stockApi.getAIAnalysis(request),
  })

  const handleAnalyze = () => {
    const cleanSymbol = symbol.trim()
    if (cleanSymbol && (analysisDimensions.length > 0 || enableAIAnalysis)) {
      if (analysisDimensions.length > 0) {
        mutation.mutate({
          symbol: cleanSymbol,
          days_ago: daysAgo,
          analysis_dimensions: analysisDimensions,
        })
      } else {
        mutation.reset()
      }

      if (enableAIAnalysis) {
        aiMutation.mutate({ symbol: cleanSymbol })
      } else {
        aiMutation.reset()
      }
    }
  }

  const formatMarketCap = (val?: number) => {
    if (!val) return '-'
    if (val >= 100000000) {
      return `${(val / 100000000).toFixed(2)}亿`
    }
    return `${(val / 10000).toFixed(2)}万`
  }

  const getSignalColor = (signal?: string) => {
    switch (signal) {
      case 'buy':
        return 'green'
      case 'sell':
        return 'red'
      default:
        return 'default'
    }
  }

  const getSignalText = (signal?: string) => {
    switch (signal) {
      case 'buy':
        return '买入'
      case 'sell':
        return '卖出'
      default:
        return '观望'
    }
  }

  const getRankColor = (rank?: string) => {
    switch (rank) {
      case 'excellent':
        return 'green'
      case 'good':
        return 'blue'
      case 'average':
        return 'orange'
      case 'poor':
        return 'red'
      default:
        return 'default'
    }
  }

  const getRankText = (rank?: string) => {
    switch (rank) {
      case 'excellent':
        return '优秀'
      case 'good':
        return '良好'
      case 'average':
        return '一般'
      case 'poor':
        return '较差'
      default:
        return '-'
    }
  }

  const getRatingColor = (rating?: string) => {
    switch (rating) {
      case '强烈推荐':
        return 'green'
      case '推荐':
        return 'blue'
      case '持有':
        return 'orange'
      case '观望':
        return 'default'
      case '回避':
        return 'red'
      default:
        return 'default'
    }
  }

  const renderTechnicalAnalysis = (data: TechnicalAnalysisResponse) => {
    const columns = [
      {
        title: '指标名称',
        dataIndex: 'name',
        key: 'name',
        width: 120,
      },
      {
        title: '当前值',
        dataIndex: 'value',
        key: 'value',
        width: 100,
        render: (val: number) => val?.toFixed?.(2) || '-',
      },
      {
        title: '信号',
        dataIndex: 'signal',
        key: 'signal',
        width: 100,
        render: (signal: string) => (
          <Tag color={getSignalColor(signal)}>
            {getSignalText(signal)}
          </Tag>
        ),
      },
      {
        title: '说明',
        dataIndex: 'description',
        key: 'description',
      },
    ]

    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Row gutter={16}>
          <Col span={8}>
            <Card>
              <Statistic
                title="当前价格"
                value={data.current_price || 0}
                precision={2}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="涨跌幅"
                value={data.change_percent || 0}
                precision={2}
                suffix="%"
                valueStyle={{ color: (data.change_percent || 0) >= 0 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic title="指标数量" value={data.indicators.length} />
            </Card>
          </Col>
        </Row>

        {data.summary && (
          <Alert
            message="技术分析总结"
            description={data.summary}
            type="info"
            showIcon
          />
        )}

        {data.kline_data && data.kline_data.length > 0 && (
          <Card style={{ marginBottom: 16 }}>
            <KlineChart data={data.kline_data} title={`${data.name || data.symbol} - 历史K线`} />
          </Card>
        )}

        <Table
          dataSource={data.indicators}
          columns={columns}
          rowKey="name"
          pagination={false}
        />
      </Space>
    )
  }

  const renderFundamentalAnalysis = (data: FundamentalAnalysisResponse) => {
    const columns = [
      {
        title: '指标名称',
        dataIndex: 'name',
        key: 'name',
        width: 150,
      },
      {
        title: '数值',
        dataIndex: 'value',
        key: 'value',
        width: 100,
        render: (val: number, record: any) =>
          val !== undefined ? `${val.toFixed(2)}${record.unit || ''}` : '-',
      },
      {
        title: '评级',
        dataIndex: 'rank',
        key: 'rank',
        width: 100,
        render: (rank: string) => (
          <Tag color={getRankColor(rank)}>{getRankText(rank)}</Tag>
        ),
      },
      {
        title: '说明',
        dataIndex: 'description',
        key: 'description',
      },
    ]

    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic title="市盈率(PE)" value={data.pe_ratio || 0} precision={2} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="市净率(PB)" value={data.pb_ratio || 0} precision={2} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="ROE" value={data.roe || 0} precision={2} suffix="%" />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="市值" value={formatMarketCap(data.market_cap)} />
            </Card>
          </Col>
        </Row>

        {data.summary && (
          <Alert
            message="基本面分析总结"
            description={data.summary}
            type="info"
            showIcon
          />
        )}

        <Table
          dataSource={data.metrics}
          columns={columns}
          rowKey="name"
          pagination={false}
        />
      </Space>
    )
  }

  const renderPricePrediction = (data: PricePredictionResponse) => {
    return (
      <Card>
        <pre
          style={{
            margin: 0,
            whiteSpace: 'pre-wrap',
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
            fontSize: 16,
            lineHeight: 1.9,
          }}
        >
          {data.output_text}
        </pre>
      </Card>
    )
  }

  const renderComprehensiveAnalysis = (data: ComprehensiveAnalysisResponse) => {
    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        <Row gutter={16}>
          <Col span={12}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <Progress
                  type="circle"
                  percent={data.overall_score}
                  width={120}
                  format={(percent) => `${percent}分`}
                />
                <Divider style={{ margin: '16px 0' }} />
                <Tag color={getRatingColor(data.overall_rating)} style={{ fontSize: 16, padding: '4px 16px' }}>
                  {data.overall_rating}
                </Tag>
              </div>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="各维度评分">
              <Space direction="vertical" style={{ width: '100%' }}>
                {data.scores.map((score, index) => (
                  <div key={index}>
                    <Row justify="space-between">
                      <Text>{score.category}</Text>
                      <Text strong>{score.score}分</Text>
                    </Row>
                    <Progress percent={score.score} showInfo={false} />
                  </div>
                ))}
              </Space>
            </Card>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Card title="风险提示" type="inner">
              <List
                dataSource={data.risks}
                renderItem={(item) => <List.Item>⚠️ {item}</List.Item>}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card title="投资机会" type="inner">
              <List
                dataSource={data.opportunities}
                renderItem={(item) => <List.Item>📈 {item}</List.Item>}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card title="操作建议" type="inner">
              <List
                dataSource={data.recommendations}
                renderItem={(item) => <List.Item>💡 {item}</List.Item>}
              />
            </Card>
          </Col>
        </Row>
      </Space>
    )
  }

  const renderAIAnalysis = () => {
    if (aiMutation.isPending) {
      return (
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
          <Spin size="large">
            <div style={{ marginTop: 16, color: '#1677ff' }}>
              AI正在深度分析基本面与技术面，这可能需要几十秒，请耐心等待...
            </div>
          </Spin>
        </div>
      )
    }

    if (aiMutation.isError) {
      return (
        <Alert
          message="AI分析失败"
          description={(aiMutation.error as Error)?.message || '请稍后重试'}
          type="error"
          showIcon
        />
      )
    }

    if (aiMutation.isSuccess && aiMutation.data) {
      return (
        <Card>
          <div className="markdown-body" style={{ padding: '0 10px' }}>
            <style>
              {`
                .markdown-body h1, .markdown-body h2, .markdown-body h3 { margin-top: 1em; margin-bottom: 0.5em; font-weight: 600; }
                .markdown-body h1 { font-size: 2em; border-bottom: 1px solid #f0f0f0; padding-bottom: 0.3em; }
                .markdown-body h2 { font-size: 1.5em; border-bottom: 1px solid #f0f0f0; padding-bottom: 0.3em; }
                .markdown-body h3 { font-size: 1.25em; }
                .markdown-body p { margin-bottom: 1em; line-height: 1.6; }
                .markdown-body ul, .markdown-body ol { padding-left: 2em; margin-bottom: 1em; }
                .markdown-body ul { list-style-type: disc; }
                .markdown-body ol { list-style-type: decimal; }
                .markdown-body li { margin-bottom: 0.5em; }
                .markdown-body strong { font-weight: 600; }
                .markdown-body blockquote { padding: 0 1em; color: #6a737d; border-left: 0.25em solid #dfe2e5; margin-bottom: 1em; }
                .markdown-body table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
                .markdown-body th, .markdown-body td { padding: 6px 13px; border: 1px solid #dfe2e5; }
                .markdown-body tr:nth-child(2n) { background-color: #f6f8fa; }
              `}
            </style>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {aiMutation.data.ai_report}
            </ReactMarkdown>
          </div>
        </Card>
      )
    }

    return null
  }

  const analysisData = mutation.data

  const selectedDimensionOptions = [
    {
      label: '技术分析',
      value: 'technical',
    },
    {
      label: '基本面分析',
      value: 'fundamental',
    },
    {
      label: '价格预测',
      value: 'price_prediction',
    },
  ]

  const tabItems: TabsProps['items'] = [
    {
      key: 'comprehensive',
      label: <span><BarChartOutlined />综合分析</span>,
      children: analysisData ? renderComprehensiveAnalysis(analysisData) : (
        <Alert message="仅执行AI深度分析" description="当前未勾选结构化分析维度。" type="info" showIcon />
      ),
    },
  ]

  if (analysisData?.technical_analysis) {
    tabItems.push({
      key: 'technical',
      label: <span><LineChartOutlined />技术分析</span>,
      children: renderTechnicalAnalysis(analysisData.technical_analysis),
    })
  }

  if (analysisData?.fundamental_analysis) {
    tabItems.push({
      key: 'fundamental',
      label: <span><FundOutlined />基本面分析</span>,
      children: renderFundamentalAnalysis(analysisData.fundamental_analysis),
    })
  }

  if (analysisData?.price_prediction) {
    tabItems.push({
      key: 'prediction',
      label: <span><LineChartOutlined />价格预测</span>,
      children: renderPricePrediction(analysisData.price_prediction),
    })
  }

  if (enableAIAnalysis) {
    tabItems.push({
      key: 'ai',
      label: <span><RobotOutlined />AI深度分析</span>,
      children: renderAIAnalysis(),
    })
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={2}><BarChartOutlined /> 股票分析</Title>
        <Paragraph>
          按需组合技术面、基本面、价格预测和AI深度分析，减少无关数据请求
        </Paragraph>
      </Card>

      <Card title="分析设置">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Paragraph>股票代码</Paragraph>
              <Input
                placeholder="请输入股票代码，如：000001"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                onPressEnter={handleAnalyze}
                size="large"
              />
            </Col>
            <Col span={12}>
              <Paragraph>分析天数：{daysAgo}天</Paragraph>
              <Input
                type="number"
                min={30}
                max={365}
                value={daysAgo}
                onChange={(e) => setDaysAgo(parseInt(e.target.value) || 60)}
                size="large"
              />
            </Col>
          </Row>
          <Divider style={{ margin: '8px 0' }} />
          <Row gutter={[16, 12]} align="middle">
            <Col xs={24} md={4}>
              <Text strong><SlidersOutlined /> 分析维度</Text>
            </Col>
            <Col xs={24} md={20}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Checkbox.Group
                  options={selectedDimensionOptions}
                  value={analysisDimensions}
                  onChange={(values) => setAnalysisDimensions(values as AnalysisDimension[])}
                />
                <Checkbox
                  checked={enableAIAnalysis}
                  onChange={(event) => setEnableAIAnalysis(event.target.checked)}
                >
                  AI深度分析
                </Checkbox>
                <Text type="secondary">
                  只会请求已勾选的维度；未勾选的模块不会拉取源数据，也不会出现在结果页。
                </Text>
              </Space>
            </Col>
          </Row>
          {analysisDimensions.length === 0 && !enableAIAnalysis && (
            <Alert message="请至少选择一个分析维度" type="warning" showIcon />
          )}
          <Button
            type="primary"
            onClick={handleAnalyze}
            loading={mutation.isPending || aiMutation.isPending}
            disabled={analysisDimensions.length === 0 && !enableAIAnalysis}
            size="large"
          >
            开始分析
          </Button>
        </Space>
      </Card>

      {mutation.isError && (
        <Alert
          message="分析失败"
          description={(mutation.error as Error)?.message || '请稍后重试'}
          type="error"
          showIcon
        />
      )}

      {((mutation.isSuccess && analysisData) || enableAIAnalysis) && (mutation.isSuccess || aiMutation.isPending || aiMutation.isSuccess || aiMutation.isError) && (
        <Card title={`分析结果 - ${analysisData?.name || analysisData?.symbol || symbol}`}>
          <Spin spinning={mutation.isPending}>
            <Tabs items={tabItems} defaultActiveKey="comprehensive" />
          </Spin>
        </Card>
      )}
    </Space>
  )
}
