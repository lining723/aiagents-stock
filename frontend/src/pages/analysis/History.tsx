import { useState } from 'react'
import { Card, Typography, Table, Button, Space, Popconfirm, Modal, message, Spin } from 'antd'
import { EyeOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { stockApi } from '@/services/stockApi'
import type { AnalysisHistoryItem } from '@/types/stock'
import dayjs from 'dayjs'

const { Title, Paragraph } = Typography

export default function AnalysisHistory() {
  const queryClient = useQueryClient()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [currentHistoryId, setCurrentHistoryId] = useState<string | null>(null)

  const { data: historyData, isLoading: isListLoading } = useQuery({
    queryKey: ['analysisHistory'],
    queryFn: () => stockApi.getAnalysisHistory(50, 0),
  })

  const { data: detailData, isLoading: isDetailLoading } = useQuery({
    queryKey: ['analysisHistoryDetail', currentHistoryId],
    queryFn: () => currentHistoryId ? stockApi.getAnalysisHistoryDetail(currentHistoryId) : null,
    enabled: !!currentHistoryId,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => stockApi.deleteAnalysisHistory(id),
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['analysisHistory'] })
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message || '未知错误'}`)
    },
  })

  const handleView = (id: string) => {
    setCurrentHistoryId(id)
    setIsModalVisible(true)
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id)
  }

  const handleModalClose = () => {
    setIsModalVisible(false)
    // 延迟清除当前 ID，防止弹窗关闭时内容突然闪烁
    setTimeout(() => setCurrentHistoryId(null), 300)
  }

  const columns = [
    {
      title: '分析时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
      width: 180,
    },
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
    },
    {
      title: '股票名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: AnalysisHistoryItem) => (
        <Space size="middle">
          <Button
            type="primary"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleView(record.id)}
          >
            查看详情
          </Button>
          <Popconfirm
            title="确定要删除这条分析记录吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button danger icon={<DeleteOutlined />} size="small">
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
        <Title level={2} style={{ margin: 0 }}>分析历史</Title>
        <Paragraph style={{ margin: 0, marginTop: 8 }}>
          查看您之前生成的所有 AI 深度分析报告。
        </Paragraph>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={historyData?.items || []}
          rowKey="id"
          loading={isListLoading}
          pagination={{ defaultPageSize: 10 }}
        />
      </Card>

      <Modal
        title={detailData?.data ? `${detailData.data.name || ''} (${detailData.data.symbol}) - AI 分析报告` : '分析报告详情'}
        open={isModalVisible}
        onCancel={handleModalClose}
        footer={[
          <Button key="close" onClick={handleModalClose}>
            关闭
          </Button>
        ]}
        width={800}
        bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
      >
        {isDetailLoading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin size="large" tip="正在加载报告详情..." />
          </div>
        ) : detailData?.data?.ai_report ? (
          <div className="markdown-body" style={{ padding: '0 10px' }}>
            <style>
              {`
                .markdown-body h1, .markdown-body h2, .markdown-body h3 { margin-top: 1em; margin-bottom: 0.5em; font-weight: 600; }
                .markdown-body h1 { font-size: 1.8em; border-bottom: 1px solid #f0f0f0; padding-bottom: 0.3em; }
                .markdown-body h2 { font-size: 1.4em; border-bottom: 1px solid #f0f0f0; padding-bottom: 0.3em; }
                .markdown-body h3 { font-size: 1.2em; }
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
              {detailData.data.ai_report}
            </ReactMarkdown>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '50px 0', color: '#999' }}>
            暂无报告内容
          </div>
        )}
      </Modal>
    </Space>
  )
}
