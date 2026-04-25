import { useState } from 'react'
import {
  Card,
  Typography,
  Button,
  Radio,
  DatePicker,
  Slider,
  Alert,
  Space,
  Row,
  Col,
  Tag,
  Divider,
  List,
  Statistic,
  Collapse,
} from 'antd'
import { FireOutlined, CalendarOutlined, ClockCircleOutlined, TrophyOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { longhubangApi } from '@/services/longhubangApi'
import type { LonghubangAnalysisRequest, RecommendedStock } from '@/types/longhubang'
import dayjs from 'dayjs'

const { Title, Paragraph, Text } = Typography

export default function LonghubangAnalysis() {
  const queryClient = useQueryClient()
  const [analysisMode, setAnalysisMode] = useState<string>('最近天数')
  const [date, setDate] = useState<string>()
  const [days, setDays] = useState<number>(1)

  const mutation = useMutation({
    mutationFn: longhubangApi.analyze,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['longhubangReports'] })
    },
  })

  const handleAnalyze = () => {
    const request: LonghubangAnalysisRequest = {
      analysis_mode: analysisMode,
      days: days,
    }
    if (analysisMode === '指定日期' && date) {
      request.date = date
    }
    mutation.mutate(request)
  }

  const renderDataInfo = (dataInfo: Record<string, any>) => {
    if (!dataInfo) return null
    return (
      <Card title="数据概览" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="上榜股票" value={dataInfo.stock_count || 0} prefix={<FireOutlined />} />
          </Col>
          <Col span={6}>
            <Statistic title="游资席位" value={dataInfo.youzi_count || 0} prefix={<TrophyOutlined />} />
          </Col>
          <Col span={6}>
            <Statistic title="买入总额" value={dataInfo.buy_total || 0} suffix="万" precision={2} />
          </Col>
          <Col span={6}>
            <Statistic title="卖出总额" value={dataInfo.sell_total || 0} suffix="万" precision={2} />
          </Col>
        </Row>
      </Card>
    )
  }

  const renderAgentsAnalysis = (agentsAnalysis: Record<string, any>) => {
    if (!agentsAnalysis) return null
    const items = Object.entries(agentsAnalysis).map(([key, value]) => ({
      key,
      label: <Text strong>{key}</Text>,
      children: <Paragraph>{typeof value === 'string' ? value : JSON.stringify(value)}</Paragraph>,
    }))
    return (
      <Card title="分析师团队分析" size="small" style={{ marginBottom: 16 }}>
        <Collapse items={items} defaultActiveKey={items.map((_, i) => i.toString())} />
      </Card>
    )
  }

  const renderFinalReport = (finalReport: Record<string, any>) => {
    if (!finalReport) return null
    return (
      <Card title="综合报告" size="small" style={{ marginBottom: 16 }}>
        <Paragraph>{finalReport.summary || finalReport.content || '暂无综合报告'}</Paragraph>
      </Card>
    )
  }

  const renderRecommendedStocks = (stocks: RecommendedStock[]) => {
    if (!stocks || stocks.length === 0) return null
    return (
      <Card title={`推荐股票 (${stocks.length} 只)`} size="small">
        <List
          dataSource={stocks}
          renderItem={(stock, index) => (
            <List.Item>
              <List.Item.Meta
                avatar={
                  <Tag color={index < 3 ? 'gold' : 'blue'}>
                    {index < 3 ? `TOP ${index + 1}` : index + 1}
                  </Tag>
                }
                title={
                  <Space>
                    <Text strong>{stock.stock_name}</Text>
                    <Text type="secondary">{stock.stock_code}</Text>
                    {stock.confidence && (
                      <Tag color="green">置信度: {stock.confidence}%</Tag>
                    )}
                  </Space>
                }
                description={stock.reason}
              />
            </List.Item>
          )}
        />
      </Card>
    )
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={2}><FireOutlined /> 龙虎榜分析</Title>
        <Paragraph>
          智瞰龙虎 — 基于AI多维度分析龙虎榜数据，挖掘游资动向与投资机会
        </Paragraph>
      </Card>

      <Card title="分析设置">
        <Space direction="vertical" style={{ width: '100%' }}>
          <Radio.Group
            value={analysisMode}
            onChange={(e) => setAnalysisMode(e.target.value)}
            style={{ marginBottom: 16 }}
          >
            <Radio.Button value="最近天数"><ClockCircleOutlined /> 最近天数</Radio.Button>
            <Radio.Button value="指定日期"><CalendarOutlined /> 指定日期</Radio.Button>
          </Radio.Group>

          {analysisMode === '最近天数' ? (
            <div>
              <Paragraph>分析天数：{days} 天</Paragraph>
              <Slider
                min={1}
                max={7}
                value={days}
                onChange={setDays}
              />
            </div>
          ) : (
            <div>
              <Paragraph>选择日期：</Paragraph>
              <DatePicker
                style={{ width: '100%' }}
                onChange={(_, dateString) => setDate(typeof dateString === 'string' ? dateString : dateString[0])}
                disabledDate={(current) =>
                  !!current && (
                    current > dayjs().endOf('day') ||
                    current.day() === 0 ||
                    current.day() === 6
                  )
                }
              />
            </div>
          )}

          <Button
            type="primary"
            onClick={handleAnalyze}
            loading={mutation.isPending}
            size="large"
            icon={<FireOutlined />}
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

      {mutation.isSuccess && mutation.data?.success && (
        <>
          <Card title="分析完成">
            <Alert
              message={mutation.data.message}
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
            {mutation.data.report_id && (
              <Paragraph type="secondary">报告ID: {mutation.data.report_id}</Paragraph>
            )}
          </Card>

          <Divider />

          {renderDataInfo(mutation.data.data_info || {})}
          {renderAgentsAnalysis(mutation.data.agents_analysis || {})}
          {renderFinalReport(mutation.data.final_report || {})}
          {renderRecommendedStocks(mutation.data.recommended_stocks || [])}
        </>
      )}

      {mutation.isSuccess && !mutation.data?.success && (
        <Alert
          message="分析未成功"
          description={mutation.data?.message || '请稍后重试'}
          type="warning"
          showIcon
        />
      )}
    </Space>
  )
}
