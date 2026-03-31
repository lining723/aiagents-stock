import { useState } from 'react'
import {
  Card,
  Typography,
  Table,
  Button,
  Space,
  Tag,
  Popconfirm,
  Modal,
  Spin,
  Alert,
  List,
  Statistic,
  Row,
  Col,
  Collapse,
} from 'antd'
import { HistoryOutlined, DeleteOutlined, EyeOutlined, FireOutlined, TrophyOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { longhubangApi } from '@/services/longhubangApi'
import type { LonghubangReportInfo, LonghubangReportDetail, RecommendedStock } from '@/types/longhubang'
import dayjs from 'dayjs'

const { Title, Paragraph, Text } = Typography

export default function LonghubangHistory() {
  const queryClient = useQueryClient()
  const [selectedReport, setSelectedReport] = useState<LonghubangReportDetail | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['longhubangReports'],
    queryFn: longhubangApi.getReports,
  })

  const deleteMutation = useMutation({
    mutationFn: longhubangApi.deleteReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['longhubangReports'] })
    },
  })

  const handleViewReport = async (reportId: string) => {
    try {
      const report = await longhubangApi.getReportDetail(reportId)
      setSelectedReport(report || null)
      setIsModalOpen(true)
    } catch (err) {
      console.error('获取报告详情失败:', err)
    }
  }

  const handleDeleteReport = (reportId: string) => {
    deleteMutation.mutate(reportId)
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

  const columns = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      width: 120,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '股票数量',
      dataIndex: 'stock_count',
      key: 'stock_count',
      width: 100,
      render: (count: number) => <Tag color="blue">{count}</Tag>,
    },
    {
      title: '游资数量',
      dataIndex: 'youzi_count',
      key: 'youzi_count',
      width: 100,
      render: (count: number) => <Tag color="orange">{count}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 160,
      render: (_: any, record: LonghubangReportInfo) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewReport(record.report_id)}
          >
            查看
          </Button>
          <Popconfirm
            title="确定要删除这个报告吗？"
            onConfirm={() => handleDeleteReport(record.report_id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              loading={deleteMutation.isPending}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={2}><HistoryOutlined /> 历史报告</Title>
        <Paragraph>
          查看和管理龙虎榜分析历史报告
        </Paragraph>
      </Card>

      {isError && (
        <Alert
          message="获取报告列表失败"
          description={(error as Error)?.message || '请稍后重试'}
          type="error"
          showIcon
        />
      )}

      <Card title="报告列表">
        <Spin spinning={isLoading}>
          <Table
            dataSource={data?.reports || []}
            columns={columns}
            rowKey="report_id"
            pagination={{ pageSize: 10 }}
            locale={{
              emptyText: '暂无历史报告，请先进行龙虎榜分析',
            }}
          />
        </Spin>
      </Card>

      <Modal
        title={`报告详情 - ${selectedReport?.date || ''}`}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={[
          <Button key="close" onClick={() => setIsModalOpen(false)}>
            关闭
          </Button>,
        ]}
        width={800}
      >
        {selectedReport && (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Paragraph type="secondary">
              报告ID: {selectedReport.report_id} | 创建时间: {dayjs(selectedReport.created_at).format('YYYY-MM-DD HH:mm:ss')}
            </Paragraph>
            {renderDataInfo(selectedReport.data_info || {})}
            {renderAgentsAnalysis(selectedReport.agents_analysis || {})}
            {renderFinalReport(selectedReport.final_report || {})}
            {renderRecommendedStocks(selectedReport.recommended_stocks || [])}
          </Space>
        )}
      </Modal>
    </Space>
  )
}
