import { Card, Typography, Table, Button, Space, Tag, Popconfirm, message } from 'antd'
import { ReloadOutlined, CheckCircleOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { monitorApi } from '@/services/monitorApi'

const { Title, Paragraph } = Typography

export default function MonitorNotifications() {
  const queryClient = useQueryClient()

  const { data: notificationsData, isLoading, refetch } = useQuery({
    queryKey: ['monitorNotifications'],
    queryFn: () => monitorApi.getNotifications(50),
  })

  const markReadMutation = useMutation({
    mutationFn: monitorApi.markNotificationsRead,
    onSuccess: (data) => {
      message.success(data?.message || '已全部标为已读')
      queryClient.invalidateQueries({ queryKey: ['monitorNotifications'] })
    },
    onError: (error: any) => {
      message.error(`操作失败: ${error.message || '未知错误'}`)
    },
  })

  const clearMutation = useMutation({
    mutationFn: monitorApi.clearNotifications,
    onSuccess: (data) => {
      message.success(data?.message || '通知已清空')
      queryClient.invalidateQueries({ queryKey: ['monitorNotifications'] })
    },
    onError: (error: any) => {
      message.error(`清空失败: ${error.message || '未知错误'}`)
    },
  })

  const handleRefresh = () => {
    refetch()
    message.success('已刷新')
  }

  const handleMarkRead = () => {
    markReadMutation.mutate()
  }

  const handleClear = () => {
    clearMutation.mutate()
  }

  const columns = [
    {
      title: '触发时间',
      dataIndex: 'triggered_at',
      key: 'triggered_at',
      width: 180,
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
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string) => {
        let color = 'blue'
        if (type === 'buy_signal') color = 'green'
        else if (type === 'sell_signal') color = 'red'
        else if (type === 'stop_loss') color = 'volcano'
        else if (type === 'take_profit') color = 'gold'
        return <Tag color={color}>{type}</Tag>
      },
    },
    {
      title: '消息内容',
      dataIndex: 'message',
      key: 'message',
    },
    {
      title: '状态',
      dataIndex: 'sent',
      key: 'sent',
      width: 100,
      render: (sent: boolean) => (
        <Tag color={sent ? 'success' : 'default'}>
          {sent ? '已读/已发' : '未读'}
        </Tag>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>提醒通知</Title>
            <Paragraph style={{ margin: 0, marginTop: 8 }}>
              查看智能盯盘引擎触发的各类价格预警和交易信号。
            </Paragraph>
          </div>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
              刷新
            </Button>
            <Button
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={handleMarkRead}
              loading={markReadMutation.isPending}
            >
              全部标为已读
            </Button>
            <Popconfirm
              title="确定要清空所有通知记录吗？此操作不可恢复。"
              onConfirm={handleClear}
              okText="确定"
              cancelText="取消"
            >
              <Button danger icon={<DeleteOutlined />} loading={clearMutation.isPending}>
                清空通知
              </Button>
            </Popconfirm>
          </Space>
        </Space>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={notificationsData?.notifications || []}
          rowKey="id"
          loading={isLoading}
          pagination={{ defaultPageSize: 20 }}
        />
      </Card>
    </Space>
  )
}
