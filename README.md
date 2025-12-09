# AI 个人化播客 App - 设计稿

基于 PRD 实现的完整、可交互的设计稿，采用 Analog OS 设计风格。

## 设计风格

参考 Theme.jsx 的设计理念，融合了：
- **Weber Precision**: 极简黑与精密加工
- **Hardy Heritage**: 复古机械与结构外露
- **Snowpeak Canvas**: 自然色（象牙白）与包容感
- **Andwander Utility**: 说明书式排版

## 功能实现

### 已实现的核心功能（P0）

1. **每日电台首页**
   - 今日推荐节目展示
   - 历史归档
   - 节目卡片（标题、时长、标签、章节）

2. **播放器**
   - 播放/暂停控制
   - 进度条拖拽
   - 15秒后退/30秒快进
   - 倍速调节（0.8x - 2.0x）
   - 音量控制

3. **节目详情页**
   - 完整脚本展示
   - 章节导航
   - 内容来源列表
   - 收藏、下载、分享功能
   - 反馈机制
   - 深度研究生成入口

4. **素材箱（信息采集）**
   - 内容列表展示
   - 手动添加（链接/文本）
   - Newsletter 专属邮箱展示
   - 标签和优先级管理
   - 状态筛选（已处理/处理中/待处理）

5. **设置页面**
   - 内容偏好设置（话题、场景、时长）
   - 声音设置（声线、语速、背景音）
   - 生成设置（时间、数量、通知）
   - Newsletter 邮箱管理
   - 账户信息
   - 使用统计

6. **搜索功能**
   - 关键词搜索
   - 类型筛选（节目/内容/主题）
   - 时间范围筛选
   - 结果分类展示

## 技术栈

- React 18
- React Router 6
- Vite
- Tailwind CSS
- Lucide React Icons

## 运行项目

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm preview
```

## 项目结构

```
/workspace
├── src/
│   ├── components/
│   │   ├── DesignSystem.jsx    # 设计系统组件库
│   │   └── Player.jsx          # 播放器组件
│   ├── pages/
│   │   ├── DailyStation.jsx    # 每日电台首页
│   │   ├── EpisodeDetail.jsx   # 节目详情页
│   │   ├── InboxPage.jsx       # 素材箱页面
│   │   ├── SettingsPage.jsx    # 设置页面
│   │   └── SearchPage.jsx      # 搜索页面
│   ├── App.jsx                 # 主应用组件
│   ├── main.jsx                # 入口文件
│   └── index.css               # 全局样式
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## 设计特点

1. **机械感 UI 控件**
   - 按钮带有"加工"质感
   - 滑块采用刻度盘设计
   - 开关具有机械感

2. **等宽字体**
   - 大量使用 Monospace 字体
   - 标签化设计
   - 规格说明风格

3. **色彩系统**
   - 背景：象牙白 (#F4F2ED)
   - 主色：哑光黑 (#1A1A1A)
   - 强调色：橙色 (#EA580C)
   - 边框：浅灰 (#D4D4D0)

4. **交互细节**
   - 悬停状态过渡
   - 点击反馈动画
   - 卡片阴影层次

## 注意事项

- 当前为设计稿阶段，使用 Mock 数据
- 所有功能均可交互，但数据未持久化
- 播放器为模拟播放，实际需要接入音频 API

## 后续开发建议

1. 接入后端 API
2. 实现真实的音频播放
3. 添加用户认证
4. 实现数据持久化
5. 优化移动端体验
6. 添加更多动画效果
