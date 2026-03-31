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
  Form,
  Input,
  InputNumber,
  Select,
  Switch,
  message,
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { monitorApi } from '@/services/monitorApi'
import type { MonitoredStock, MonitoredStockCreate, MonitoredStockUpdate } from '@/types/monitor'

const { Title, Paragraph } = Typography
const { Option } = Select

export default function MonitorStocks() {
  const queryClient = useQueryClient()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [editingStock, setEditingStock] = useState<MonitoredStock | null>(null)
  const [form] = Form.useForm()

  const { data: stocksData, isLoading } = useQuery({
    queryKey: ['monitoredStocks'],
    queryFn: monitorApi.getStocks,
  })

  const addMutation = useMutation({
    mutationFn: (values: MonitoredStockCreate) => monitorApi.addStock(values),
    onSuccess: () => {
      message.success('添加成功')
      setIsModalVisible(false)
      queryClient.invalidateQueries({ queryKey: ['monitoredStocks'] })
    },
    onError: (error: any) => {
      message.error(`添加失败: ${error.message || '未知错误'}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: MonitoredStockUpdate }) =>
      monitorApi.updateStock(id, values),
    onSuccess: () => {
      message.success('更新成功')
      setIsModalVisible(false)
      queryClient.invalidateQueries({ queryKey: ['monitoredStocks'] })
    },
    onError: (error: any) => {
      message.error(`更新失败: ${error.message || '未知错误'}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => monitorApi.deleteStock(id),
    onSuccess: () => {
      message.success('删除成功')
      queryClient.invalidateQueries({ queryKey: ['monitoredStocks'] })
    },
    onError: (error: any) => {
      message.error(`删除失败: ${error.message || '未知错误'}`)
    },
  })

  const handleAdd = () => {
    setEditingStock(null)
    form.resetFields()
    form.setFieldsValue({
      check_interval: 300,
      notification_enabled: true,
      trading_hours_only: true,
      quant_enabled: false,
      rating: '持有',
    })
    setIsModalVisible(true)
  }

  const handleEdit = (record: MonitoredStock) => {
    setEditingStock(record)
    form.setFieldsValue({
      ...record,
      min_entry: record.entry_range?.min,
      max_entry: record.entry_range?.max,
    })
    setIsModalVisible(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleModalOk = () => {
    form.validateFields().then((values) => {
      const payload = {
        symbol: values.symbol,
        name: values.name,
        rating: values.rating,
        entry_range: {
          min: values.min_entry || 0,
          max: values.max_entry || 0,
        },
        take_profit: values.take_profit,
        stop_loss: values.stop_loss,
        check_interval: values.check_interval,
        notification_enabled: values.notification_enabled,
        trading_hours_only: values.trading_hours_only,
        quant_enabled: values.quant_enabled,
      }

      if (editingStock) {
        updateMutation.mutate({ id: editingStock.id, values: payload })
      } else {
        addMutation.mutate(payload as MonitoredStockCreate)
      }
    })
  }

  const columns = [
    {
      title: '代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '评级',
      dataIndex: 'rating',
      key: 'rating',
      render: (rating: string) => {
        let color = 'default'
        if (rating === '强烈推荐') color = 'green'
        else if (rating === '推荐') color = 'blue'
        else if (rating === '持有') color = 'orange'
        else if (rating === '回避') color = 'red'
        return <Tag color={color}>{rating}</Tag>
      },
    },
    {
      title: '当前价',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (price: number) => (price ? price.toFixed(2) : '-'),
    },
    {
      title: '目标区间',
      key: 'entry_range',
      render: (_: any, record: MonitoredStock) => {
        const { min, max } = record.entry_range || {}
        if (min && max) return `${min} - ${max}`
        return '-'
      },
    },
    {
      title: '止损/止盈',
      key: 'sl_tp',
      render: (_: any, record: MonitoredStock) => (
        <Space direction="vertical" size="small">
          <span style={{ color: '#cf1322' }}>损: {record.stop_loss || '-'}</span>
          <span style={{ color: '#3f8600' }}>盈: {record.take_profit || '-'}</span>
        </Space>
      ),
    },
    {
      title: '状态',
      key: 'status',
      render: (_: any, record: MonitoredStock) => (
        <Space direction="vertical" size="small">
          <Tag color={record.notification_enabled ? 'success' : 'default'}>
            {record.notification_enabled ? '通知开' : '通知关'}
          </Tag>
          <Tag color={record.trading_hours_only ? 'processing' : 'warning'}>
            {record.trading_hours_only ? '仅交易时段' : '全天候'}
          </Tag>
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: MonitoredStock) => (
        <Space size="middle">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确定要删除此监测股票吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>监测股票</Title>
            <Paragraph style={{ margin: 0, marginTop: 8 }}>
              管理您的自选股监控列表，设置目标价格区间和止盈止损线。
            </Paragraph>
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd} size="large">
            添加监测
          </Button>
        </Space>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={stocksData?.stocks || []}
          rowKey="id"
          loading={isLoading}
          pagination={{ defaultPageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingStock ? '编辑监测股票' : '添加监测股票'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        confirmLoading={addMutation.isPending || updateMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Space size="large" style={{ display: 'flex', width: '100%' }}>
            <Form.Item
              name="symbol"
              label="股票代码"
              rules={[{ required: true, message: '请输入股票代码' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="如: 000001" disabled={!!editingStock} />
            </Form.Item>
            <Form.Item
              name="name"
              label="股票名称"
              rules={[{ required: true, message: '请输入股票名称' }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="如: 平安银行" disabled={!!editingStock} />
            </Form.Item>
          </Space>

          <Space size="large" style={{ display: 'flex', width: '100%' }}>
            <Form.Item
              name="min_entry"
              label="目标买入最低价"
              style={{ flex: 1 }}
            >
              <InputNumber style={{ width: '100%' }} precision={2} />
            </Form.Item>
            <Form.Item
              name="max_entry"
              label="目标买入最高价"
              style={{ flex: 1 }}
            >
              <InputNumber style={{ width: '100%' }} precision={2} />
            </Form.Item>
          </Space>

          <Space size="large" style={{ display: 'flex', width: '100%' }}>
            <Form.Item
              name="stop_loss"
              label="止损价"
              style={{ flex: 1 }}
            >
              <InputNumber style={{ width: '100%' }} precision={2} />
            </Form.Item>
            <Form.Item
              name="take_profit"
              label="止盈价"
              style={{ flex: 1 }}
            >
              <InputNumber style={{ width: '100%' }} precision={2} />
            </Form.Item>
          </Space>

          <Space size="large" style={{ display: 'flex', width: '100%' }}>
            <Form.Item
              name="rating"
              label="评级"
              style={{ flex: 1 }}
            >
              <Select>
                <Option value="强烈推荐">强烈推荐</Option>
                <Option value="推荐">推荐</Option>
                <Option value="持有">持有</Option>
                <Option value="观望">观望</Option>
                <Option value="回避">回避</Option>
              </Select>
            </Form.Item>
            <Form.Item
              name="check_interval"
              label="检查间隔(秒)"
              style={{ flex: 1 }}
            >
              <InputNumber style={{ width: '100%' }} min={10} />
            </Form.Item>
          </Space>

          <Space size="large" style={{ display: 'flex', width: '100%' }}>
            <Form.Item
              name="notification_enabled"
              label="开启通知"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
            <Form.Item
              name="trading_hours_only"
              label="仅交易时段监测"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
            <Form.Item
              name="quant_enabled"
              label="启用量化交易"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </Space>
  )
}
