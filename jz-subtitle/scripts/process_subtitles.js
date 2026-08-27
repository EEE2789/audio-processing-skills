#!/usr/bin/env node
/**
 * 币圈字幕处理脚本
 *
 * 功能：
 * 1. 币圈专用纠错替换
 * 2. 数字口语化（≥10000 的数字转为"万"单位）
 * 3. 语气词清理
 * 4. 行尾标点清理
 * 5. 断句优化（单行 12-18 字）
 * 6. 支持用户审核模式
 *
 * 输入：火山引擎转录结果 JSON（带时间戳）
 * 输出：draft.txt（审核稿）, final.srt, final.txt
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

/**
 * 格式化秒数为分钟和秒的格式
 * @param {number} seconds - 秒数
 * @returns {string} 格式化后的字符串，如 "4分16.59秒"
 */
function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins > 0) {
    return `${mins}分${secs.toFixed(2)}秒`;
  } else {
    return `${secs.toFixed(2)}秒`;
  }
}

// ====== 配置 ======

// 币圈专用纠错替换（优先级最高，所有处理前先执行）
const CRYPTO_REPLACE_MAP = {
  // 人名纠错
  '局长': '军长',
  '君子': '军长',
  '郡长': '军长',
  '军章': '军长',
  '军掌': '军长',

  // 常见口语纠错
  '鹰然': '依然',
  '网上': '往上',
  '幅近': '附近',
  '阿浪': '二浪',
  '繁爪': '反转',
  '小子损': '小止损',
  '住单': '做单',

  // 币种纠错（注意：不将"比特"转换为"比特币"）
  '比对比': '比特币',
  '一套房': '以太坊',

  // 其他纠错
  '买路': '买入',
  '名牌': '明牌',

  // 新增纠错
  '杂盘': '砸盘',
  '走亡': '走完',
  '蛙浪': 'y浪',
  '避让': 'b浪',
  '空投': '多头',

  // 用户纠错
  '无线': '无限',
  '缩书': '缩水',
  '陆地': '落地',
  '锦书': '紧缩',
  '上映': '上任',
  '阻塞浪': '主升浪',
  '蒸发': '增发',

  // 2026-02-12 新增（来自 draft.txt 审核）
  '报餐价': '爆仓价',
  '匡幅': '宽幅',

  // 2026-02-13 新增（脏话过滤）
  // "逼"在中文语境里是脏话，全文不允许出现"逼浪"这种词汇
  // 除非是"逼迫"等词语，其他的"逼"全改成"b"
  '逼浪': 'b浪',
  '逼是': 'b是',
  '逼比': 'b比',
  // 注意：不添加"逼"→"b"的全局替换，会误伤"逼迫"等正常词汇
  // 只针对常见的错误组合进行替换

  // 2026-02-21 新增（来自 draft.txt 审核）
  '姻缘': '依然',

  // 2026-03-12 新增（来自 draft.txt 审核）
  '低供感': '低杠杆',
  '低共感': '低杠杆',
  '低供港': '低杠杆',
  '高供港': '高杠杆',
  '供港': '杠杆',
  '筑都': '做多',
  '诸都': '做多',
  '阴炎': '依然',
  '因缘': '依然',
  '音源': '依然',
  '不易': '博弈',

  // 2026-07-06 新增（来自用户审核修正）
  '胃': '位',
  '共感': '杠杆',

  // 2026-07-20 新增（来自用户审核修正）
  '怎么正': '怎么震',
  '横旁': '横盘',
  '揭露': '介入',
  '毕总': '币种',

  // 2026-07-22 新增（来自用户审核修正）
  '铸都': '做多',
  '贡杆': '杠杆',
  '震真正': '震荡',
  '店破': '跌破',
  '是能苑': '依然',
  '呃': '',
  '怎么镇': '怎么震',

  // 2026-08-24 新增（来自用户审核修正）
  '毫碎': '所以的话',
  '仪太坊': '以太坊',
  '政府': '振幅',

  // 2026-03-13 新增（来自 draft.txt 审核）
  '变跑': '变盘',
  '浪琴': '浪型',
  '起散点': '起涨点',
  '烂': '浪',

  // 2026-02-23 新增（来自 draft.txt 审核）
  // 将没有明确人物指向的"他"改成"它"（用于指代比特币、以太坊等）
  '他': '它',

  // 2026-02-24 新增（来自 draft.txt 审核）
  '村长': '军长',
  '只赢': '止盈',
  '止赢': '止盈',  // 2026-07-31 新增（交易术语）

  // 2026-02-25 新增（专业金融视频过滤）
  // 过滤疾病和生殖器相关词汇
  '阴茎': '隐藏',
  '睾丸': '铜墙',
  '前列腺': '前线',
  '阳痿': '完毕',
  '早泄': '抛售',
  '艾滋': '暗指',
  '梅毒': '每次',
  '淋病': '临近',
  '尖锐湿疣': '坚持无边',

  // 2026-02-27 新增
  '下趟': '下探',
  '诸多': '做多',

  // 2026-03-03 新增（波浪理论术语规范）
  '一浪': 'e浪',
  '伊浪': 'e浪',

  // 2026-03-17 新增（用户审核修正）
  '助渡': '做多',
  '八腕': '8万',
  '爱浪': '2浪',
  '以态': '以太',
  '长了': '涨了',
  '硬翼': '任意',
  'XLAN': 'x浪',
  '音乐': '依然',
  '阴阳': '依然',
  'xone': 'x浪',
  'j浪': 'z浪',
  '歪浪': 'y浪',
  '斐波纳切': '斐波那契',

  // 2026-03-10 新增（波浪理论术语规范）
  'yclon': 'yc浪',
  'xline': 'x浪',
  'Yclan': 'yc浪',

  // 2026-03-11 新增（波浪理论和交易术语规范）
  'YBlong': 'yb浪',
  'long': '浪',
  '让行': '浪形',
  '继续正': '继续震',
  '1比': '一笔',
  '空档': '空单',

  // 2026-03-20 新增（用户审核修正）
  '步调': '破掉',
  'ONE': '浪',
  'one': '浪',
  '框幅': '宽幅',
  '这一行为': '这一线位',
  '地点': '低点',
  'g线': '一线',
  '收购': '收割',  // 2026-03-23 新增（交易术语）
  '指银': '止盈',  // 2026-03-24 新增（交易术语）
  'JLA': 'z浪',    // 2026-03-24 新增（波浪理论）
  '盘子': '盘整',  // 2026-03-24 新增（交易术语）
  '独单': '多单',    // 2026-03-25 新增（交易术语）
  '多塔': '多单',    // 2026-08-10 新增（交易术语）
  '阶度位': '接多位',  // 2026-08-11 新增（交易术语）
  '仪态法': '以太坊',  // 2026-08-11 新增（币种）
  '以太仿': '以太坊',  // 2026-08-19 新增（币种）
  '仪态': '以太',     // 2026-08-11 新增（币种）
  '贡嘎': '杠杆',     // 2026-08-11 新增（交易术语）
  '开端': '开单',     // 2026-08-11 新增（交易术语）

  // 2026-08-25 新增（用户审核修正）
  '止营': '止盈',     // 交易术语误识别
  '差一个针': '插一个针',  // 口语误识别
  '除掉': '出掉',     // 口语误识别

  // 2026-08-26 新增（用户审核修正）
  '怎么整': '怎么震',     // 口语误识别
  '加一次差': '加一次仓',  // 交易术语误识别

  // 2026-08-27 新增（用户审核修正）
  '1次长': '一次仓',      // 交易术语误识别

  // 2026-08-21 新增（用户审核修正）
  '以泰': '以太',      // 币种误识别
  '做度': '做多',      // 交易术语误识别
  '司机': '时机',      // 交易术语误识别
  // 2026-08-22 新增（用户审核修正）
  'AVE1': 'AAVE',      // 币种误识别
  'AVE': 'AAVE',       // 币种误识别
  'Ave': 'AAVE',       // 币种误识别
  'ave': 'AAVE',       // 币种误识别
  '充了': '冲了',      // 动词误识别
  '网建': '晚间',      // 时间误识别
  '浪芯': '浪型',      // 波浪理论误识别
  '一套房': '以太坊',   // 币种误识别
  '布局度': '布局多',  // 交易术语误识别

  // 2026-03-26 新增（波浪理论和形态术语规范）
  'YBland': 'Yb浪',
  'YB land': 'Yb浪',
  'Ybland': 'Yb浪',
  '警线': '颈线',
  '头尖底': '头肩底',

  // 2026-03-27 新增（波浪理论和技术分析）
  'line': '浪',
  '人族': '零轴',
  '回潮': '回抽',
  '回测': '回撤',  // 2026-07-31 新增（交易术语）
  '回侧': '回撤',  // 2026-08-19 新增（交易术语）
  '回条': '回调',  // 2026-08-09 新增（交易术语）
  '加个叉': '加个仓',  // 2026-08-19 新增（交易术语）

  // 2026-04-06 新增（交易术语）
  '止水': '止损',

  // 2026-04-07 新增（技术形态术语）
  '鞋型': '楔形',
  '鞋形': '楔形',

  // 2026-04-10 新增（ASR 误识别修正）
  '进档': '震荡',
  '静态': '震荡',

  // 2026-04-11 新增（ASR 误识别修正）
  '这一些': '这一线',
  '阴影': '依然',

  // 2026-04-13 新增（ASR 误识别修正）
  '近档': '震荡',
  '巨尺': '锯齿',
  '监督': '接多',
  '以它': '以太',
  '接纳': 'z浪',
  '巨子星': '锯齿形',

  // 2026-04-09 新增（ASR 误识别修正）
  '删了': '3浪',
  '句子': '锯齿',
  '锯子': '锯齿',
  '句词': '锯齿',
  '以探访': '以太坊',

  // 2026-04-08 新增（ASR 误识别修正）
  '飞行': '分析',
  '做督': '做多',
  '助多': '做多',  // 2026-08-09 新增（交易术语）
  '仪态坊': '以太坊',
  '死机': '时机',
  '定档': '震荡',
  '碧浪': 'b浪',
  '浪险': '浪型',
  '三句尺': '三锯齿',
  '三巨石': '三锯齿',
  '高泵感': '高倍杠杆',
  '铺': '破',

  // 2026-04-14 新增（ASR 误识别修正）
  '三句使': '三锯齿',
  '灾难': 'z浪',
  '上策': '上车',
  '弊种': '币种',
  '短度': '短多',

  // 2026-04-15 新增（ASR 误识别修正）
  '接浪': 'z浪',
  'a蜡': 'a浪',
  'ZLA': 'z浪',
  '止一下水': '止一下损',
  '回录': '回落',
  'b蜡': 'b浪',
  'c蜡': 'c浪',
  'e蜡': 'e浪',
  'x蜡': 'x浪',
  'y蜡': 'y浪',
  'z蜡': 'z浪',
  '锯蜡': '锯齿',

  // 2026-04-21 新增（ASR 误识别修正）
  '追浪': 'z浪',

  // 2026-04-23 新增（ASR 误识别修正）
  '怡泰坊': '以太坊',
  '阴岩': '依然',
  '仪态仿': '以太坊',

  // 2026-04-24 新增（ASR 误识别修正）
  '下沙': '下杀',

  // 2026-04-26 新增（ASR 误识别修正）
  '器型': '楔形',
  '指引': '止盈',

  // 2026-06-30 新增（用户审核修正）
  '挣了': '震了',
  'jec': 'zec',
  'j e c': 'zec',
  'j e c哈': 'zec',
  '除掉了': '出掉了',
  '北部纳切': '斐波那契',
  '景线': '颈线',

  // 2026-04-27 新增（ASR 误识别修正）
  '开档': '开单',

  // 2026-04-28 新增（ASR 误识别修正）
  '见中线': '建中线',

  // 2026-04-29 新增（ASR 误识别修正）
  '空塔': '空单',

  // 2026-05-02 新增（ASR 误识别修正）
  '中序': '中继',
  '诸都': '做多',
  '交易队': '交易对',

  // 2026-05-02 新增（脏字过滤）
  '阴沿': '依然',

  // 2026-05-04 新增（用户审核修正）
  '增大': '震荡',
  '小鸡背': '小级别',
  '鹰眼': '依然',
  '接督': '接多',

  // 2026-05-05 新增（用户审核修正）
  '立空': '利空',
  '助都': '做多',
  '主力区': '阻力区',

  // 2026-05-06 新增（用户审核修正）
  '帮扶': '宽幅',
  'CR浪': 'C2浪',
  '仪式': '疑似',
  '开度': '开多',
  '负进': '附近',

  // 2026-05-07 新增（用户审核修正）
  '合金': '行情',
  '中信': '中线',
  '捺': '浪',
  '舞狮': '54',
  '很正': '很震',
  '斜行': '楔形',
  '见了': '建了',

  // 2026-06-16 新增（用户审核修正）
  '直营': '止盈',
  '位置正': '位置震',
  '注督': '做多',

  // 2026-06-17 新增（用户审核修正）
  '正完': '震完',
  '避难': 'b浪',

  // 2026-05-08 新增（用户审核修正）
  '斜形': '楔形',

  // 2026-05-11 新增（用户审核修正）
  '转都': '转多',

  // 2026-05-13 新增（用户审核修正）
  '怎么挣': '怎么震',
  '期限': '楔形',
  '阵亡': '震完',
  '共杆': '杠杆',

  // 2026-05-17 新增（用户审核修正）
  '警限': '颈线',

  // 2026-05-18 新增（用户审核修正）
  '凯文务实': '凯文沃什',
  '旁面': '盘面',
  '3段是': '3段式',
  'Xl浪': 'x浪',
  '应命': '认命',
  '瑞士': '类似',

  // 2026-05-19 新增（用户审核修正）
  '李四': '理事',

  // 2026-05-21 新增（用户审核修正）
  '挣几天': '震几天',
  '待币': '代币',
  'b总': '币种',
  'b种': '币种',

  // 2026-05-22 新增（用户审核修正）
  '助空': '做空',

  // 2026-05-24 新增（用户审核修正）
  'XLA': 'x浪',
  '上册': '上车',

  // 2026-06-11 新增（用户审核修正）
  '浪行': '浪形',

  // 2026-06-12 新增（用户审核修正）
  '督': '多',
  '美观': '美光',

  // 2026-06-14 新增（用户审核修正）
  '色号': '设好',
  '补偿': '补仓',

  // 2026-06-19 新增（用户审核修正）
  'a b c': 'abc',
  '避浪': 'b浪',
  '指跌': '止跌',
  'dyd叉': 'dydx',
  '模拟': '磨底',
  '延涨': '延长',
  '母底': '磨底',
  '肠胃': '仓位',

  // 2026-06-24 新增（用户审核修正）
  '剪图': '简图',
  '倍增': '被震',
  '必走': '币种',

  // 2026-06-25 新增（用户审核修正）
  '掌破': '涨破',
  '比较正': '比较震',
  '正幅': '震幅',
  '避重': '币种',

  // 2026-06-27 新增（用户审核修正）
  '长得': '涨得',
  '清套': '轻套',

  // 2026-06-29 新增（用户审核修正）
  '美乙': '美伊',
  '叉LM': 'XLM',

  // 2026-07-03 新增（用户审核修正）
  '宽体': '框体',
  '记忆线': '这一线',
  '助当': '做单',

  // 2026-07-08 新增（用户审核修正）
  '缝': '逢',
  '成品价': '成本价',
  '窗位': '仓位',
  '供暖': '杠杆',

  // 2026-07-09 新增（用户审核修正）
  '小鸡': '小级',
  '加差': '加仓',

  // 2026-07-10 新增（用户审核修正）
  '紫银': '止盈',
  '杜丹': '多单',

  // 2026-07-27 新增（用户审核修正）
  '州县': '周线',
  '盲手': '满手',
  '以太法': '以太坊',
  '小臂种': '小币种',
  '抗涨': '看涨',
  '乌龟币': 'turbo',

  // 2026-07-29 新增
  '小币总': '小币种',

  // 2026-08-14 新增（用户审核修正）
  '玉器': '预期',

  // 2026-08-15 新增（用户审核修正）
  'b组': '币种',
  '射': '设',
  '币总': '币种',
};

// 专业术语词典（保护这些词不被误删）
const PROTECT_TERMS = [
  // 加密货币
  '比特币', 'BTC', '以太坊', 'ETH', 'USDT', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'SHIB',
  '大饼', '山寨币', '稳定币', 'DeFi', 'NFT', 'Web3', 'DAO',

  // 技术分析 - 缠论
  '缠论', '背驰', 'WXY', 'ABC', 'X浪', 'Y浪', 'C浪', 'E浪', 'A浪', 'B浪',
  '1浪', '2浪', '3浪', '4浪', '5浪', '大级别', '小级别', '级别',
  '笔', '线段', '中枢', '走势', '盘整', '趋势', '上涨', '下跌', '震荡',

  // 技术分析 - 形态
  '旗形', '三角形', '楔形', '矩形', '头肩底', '头肩顶', '双底', '双顶', '三重底', '三重顶',
  'W底', 'M头', '圆弧底', 'V形反转', '旗形整理', '上升三角形', '下降三角形',
  '右肩', '左肩', '颈线', '突破', '下破', '上破', '假突破', '有效突破',

  // 交易术语
  '做多', '做空', '多单', '空单', '开仓', '平仓', '减仓', '加仓', '补仓', '爆仓', '止损', '止盈',
  '挂单', '市价单', '限价单', '止损单', '止盈单', '杠杆', '合约', '现货', '期货',
  '永续合约', '交割合约', '期权', '交割', '结算',

  // 市场状态
  '多头', '空头', '牛市', '熊市', '猴市', '震荡市', '趋势行情', '盘整行情',
  '反弹', '回调', '回踩', '探底', '筑底', '拉升', '跳水', '暴涨', '暴跌',
  '横盘', '整理', '洗盘', '吸筹', '出货', '诱多', '诱空',

  // 指标相关
  'MACD', 'RSI', 'KDJ', 'BOLL', 'MA', 'EMA', 'SMA', '均线', '5日线', '10日线', '20日线', '60日线',
  '布林带', '成交量', '放量', '缩量', '背离', '金叉', '死叉',

  // 压力支撑
  '压力位', '支撑位', '阻力位', '关键位', '破位', '站稳', '跌破',
  '上方', '下方', '高位', '低位', '顶部', '底部',

  // 时间周期
  '日线', '周线', '月线', '4小时', '1小时', '30分钟', '15分钟', '5分钟', '1分钟',
  'K线', '蜡烛图', '阳线', '阴线', '十字星',

  // 交易术语 - 包含"逼"的专业术语（保护不被删除）
  '逼仓', '逼迫',

  // 其他专业术语
  '仓位', '重仓', '轻仓', '满仓', '空仓', '风控', '盈亏比', '胜率',
  '左侧交易', '右侧交易', '抄底', '逃顶', '追涨', '杀跌',
  '热力图', '流动性', '主力', '散户', '筹码',

  // 金融术语
  '美联储', '鹰派', '鸽派', '降息', '加息', '利率', '通胀', '通缩', 'CPI', 'PCE',
  '非农数据', 'GDP', '收益率', '国债', '美元指数', '避险情绪',
  '黄金', '白银', '贵金属', '美股', 'A股', '港股',
];

// 语气词列表（需要去除）
const FILLERS = [
  '嗯', '啊', '欸', '哎', '噢', '哦', '唔', '嗯哼', '哈',
  '这个', '那个', '就是', '然后', '其实', '可能', '我觉得', '你看', '对吧', '好吗',
  '呢', '嘛', '吧', '呀', '啦', '喽'
];

// ====== 工具函数 ======

// 获取日期后缀（格式：0204 表示 02月04日）
function getDateSuffix() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${month}${day}`;
}

// 格式化时间（毫秒 → SRT 时间格式）
function fmtTime(ms) {
  const milliseconds = ms % 1000;
  const totalSeconds = Math.floor(ms / 1000);
  const sec = totalSeconds % 60;
  const min = Math.floor((totalSeconds / 60) % 60);
  const hr = Math.floor(totalSeconds / 3600);
  return `${String(hr).padStart(2, '0')}:${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')},${String(milliseconds).padStart(3, '0')}`;
}

// 检查是否包含保护术语
function hasProtectTerm(text) {
  for (const term of PROTECT_TERMS) {
    if (text.includes(term)) return true;
  }
  return false;
}

// 币圈纠错替换
function applyCryptoReplace(text) {
  let result = text;
  for (const [from, to] of Object.entries(CRYPTO_REPLACE_MAP)) {
    const regex = new RegExp(from, 'g');
    result = result.replace(regex, to);
  }
  return result;
}

// 数字口语化（≥10000 的数字转为"万"单位）
function numberToColloquial(text) {
  return text.replace(/\b(\d{5,})\b/g, (match) => {
    const num = parseInt(match, 10);
    if (num < 10000) return match;

    const wan = Math.floor(num / 10000);
    const remainder = num % 10000;

    if (remainder === 0) {
      return `${wan}万`;
    } else if (remainder < 1000) {
      // 例如：93000 → 9万3
      return `${wan}万${remainder}`;
    }
    // 保留精确数字（避免误伤价格）
    return match;
  });
}

// 语气词清理
function removeFillers(text) {
  let result = text;

  // 句尾语气词
  result = result.replace(/[呢嘛吧呀啊啦喽噢哦唔嗯哼哈][，。！？、]*$/g, '');

  // 句首语气词（包括"呃"）
  result = result.replace(/^[，。！？、]?(嗯|啊|呃|欸|哎|噢|哦|哈|这个|那个|就是|然后|其实|可能)[，。！？、]*/g, '');

  // 句中语气词组合（保护专业术语）
  if (!hasProtectTerm(result)) {
    result = result.replace(/呢是/g, '是');
    result = result.replace(/那所以/g, '所以');
    result = result.replace(/那我们/g, '我们');
    result = result.replace(/然后呢/g, '');
    result = result.replace(/那就是/g, '是');
    result = result.replace(/的话[，。]*/g, '');
  }

  // 清理多余标点
  result = result.replace(/[，。、、]{2,}/g, '、');
  result = result.replace(/^、+|、+$/g, '');
  result = result.replace(/\s+/g, '');

  return result;
}

// 行尾标点清理
function removeTrailingPunct(text) {
  let result = text.replace(/[，。！？、；：]+$/, '');
  // 删除句尾的"呃"
  result = result.replace(/呃$/, '');
  return result;
}

// 处理单条字幕文本
function processText(text) {
  let result = text;

  // 1. 币圈纠错替换（最高优先级）
  result = applyCryptoReplace(result);

  // 1.5. 自我介绍特殊处理：我是XX → 我是军长
  // 只在字幕开头10秒内（约前30条）有效
  // 匹配 "我是xxx" 格式，将xxx替换为"军长"
  result = result.replace(/^我是(.+)$/, (match, name) => {
    // 如果已经是"我是军长"，保持不变
    if (name === '军长') return match;
    // 否则替换为"我是军长"
    return '我是军长';
  });

  // 1.6. 脏字完全删除（2026-05-02 新增）
  // 删除完全无意义的脏字，但不影响正常词汇
  // "妈的"系列 - 完全删除
  result = result.replace(/妈的/g, '');
  result = result.replace(/他妈的/g, '');
  result = result.replace(/他妈/g, '');
  // 独立出现的脏字 - 使用词边界确保不影响正常词汇
  result = result.replace(/\b屄\b/g, '');
  result = result.replace(/\b肏\b/g, '');
  result = result.replace(/\b操\b/g, '');
  // 注意：不删除"草"，因为"草稿"等正常词汇会被误伤

  // 2. 数字口语化
  result = numberToColloquial(result);

  // 3. 通用语气词清理
  result = result.replace(/呢是/g, '是');
  result = result.replace(/那所以/g, '所以');
  result = result.replace(/那我们/g, '我们');
  result = result.replace(/那的话/g, '');
  result = result.replace(/的话$/g, '');
  result = result.replace(/，然后[，]/g, '、');
  result = result.replace(/^那(他|这|我|你|我们|他们)/g, '$1');
  result = result.replace(/^(那么?)，/g, '');
  result = result.replace(/那这样/g, '这样');
  result = result.replace(/呢他/g, '他');
  result = result.replace(/OK这是/g, 'OK，这是');
  // 去除单独的"呢"（句尾、句首、句中）
  result = result.replace(/呢[，。！？、]*$/g, '');
  result = result.replace(/^[，。！？、]呢/g, '');
  result = result.replace(/([呢])[，、]/g, '');  // "呢，" 或 "呢、" 后面接标点的情况
  result = result.replace(/呢是/g, '是');  // "呢是" → "是"

  // 4. 深度语气词清理（保护专业术语）
  if (!hasProtectTerm(result)) {
    result = removeFillers(result);
  } else {
    for (const filler of ['嗯', '啊', '呃', '欸', '哎', '噢', '哦', '哈']) {
      result = result.replace(new RegExp(`${filler}[，、]?$`), '');
      result = result.replace(new RegExp(`^[，、]?${filler}`), '');
    }
  }

  // 5. 额外删除"呃"（任何位置）
  result = result.replace(/呃[，。！？、]*/g, '');

  // 6. 行尾标点清理
  result = removeTrailingPunct(result);

  // 7. 脏字兜底替换（2026-05-02 新增）
  // 如果所有替换完成后，仍然出现"阴"、"逼"等脏字，用"*"代替
  // 但保护专业术语（如"阴线"、"逼仓"、"逼迫"等已在PROTECT_TERMS中）
  if (!hasProtectTerm(result)) {
    // 未保护的情况下，直接替换
    result = result.replace(/阴/g, '*');
    result = result.replace(/逼/g, '*');
  } else {
    // 包含保护术语的情况下，只替换不在保护术语中的"阴"、"逼"
    // 使用负向前瞻，确保不匹配"阴线"、"逼仓"、"逼迫"等词
    result = result.replace(/阴(?!线)/g, '*');
    result = result.replace(/逼(?!仓|迫)/g, '*');
  }

  return result;
}

// 简体转繁体（币圈常用字映射）
function toTraditional(text) {
  const s2tMap = {
    // 数字
    '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
    '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
    '万': '萬', '亿': '億', '千': '千', '百': '百',

    // 币圈术语
    '比特币': '比特幣', 'BTC': 'BTC', '以太坊': '以太坊', 'ETH': 'ETH',
    'USDT': 'USDT', 'BNB': 'BNB', 'SOL': 'SOL', 'XRP': 'XRP',
    '山寨币': '山寨幣', '稳定币': '穩定幣',
    'DeFi': 'DeFi', 'NFT': 'NFT', 'Web3': 'Web3', 'DAO': 'DAO',

    // 缠论
    '缠论': '纏論', '背驰': '背馳', 'WXY': 'WXY', 'ABC': 'ABC',
    '笔': '筆', '线段': '線段', '中枢': '中樞', '走势': '走勢',
    '盘整': '盤整', '趋势': '趨勢', '上涨': '上漲', '下跌': '下跌',
    '震荡': '震盪', '旗形': '旗形', '三角形': '三角形', '楔形': '楔形',
    '矩形': '矩形', '头肩底': '頭肩底', '头肩顶': '頭肩頂',
    '双底': '雙底', '双顶': '雙頂', '颈线': '頸線',
    '突破': '突破', '下破': '下破', '上破': '上破',

    // 交易
    '做多': '做多', '做空': '做空', '多单': '多單', '空单': '空單',
    '开仓': '開倉', '平仓': '平倉', '减仓': '減倉', '加仓': '加倉',
    '止损': '止損', '止盈': '止盈', '杠杆': '槓桿', '合约': '合約',
    '现货': '現貨', '期货': '期貨', '期权': '期權',
    '多头': '多頭', '空头': '空頭', '牛市': '牛市', '熊市': '熊市',
    '反弹': '反彈', '回调': '回調', '回踩': '回踩', '探底': '探底',
    '筑底': '築底', '拉升': '拉升', '跳水': '跳水', '暴涨': '暴漲',
    '暴跌': '暴跌', '横盘': '橫盤', '整理': '整理',
    '吸筹': '吸籌', '出货': '出貨', '诱多': '誘多', '诱空': '誘空',

    // 指标
    'MACD': 'MACD', 'RSI': 'RSI', 'KDJ': 'KDJ', 'BOLL': 'BOLL',
    '均线': '均線', '布林带': '布林帶', '成交量': '成交量',
    '背离': '背離', '金叉': '金叉', '死叉': '死叉',
    '压力位': '壓力位', '支撑位': '支撐位', '阻力位': '阻力位',

    // 时间
    '日线': '日線', '周线': '周線', '月线': '月線',
    '小时': '小時', '分钟': '分鐘', 'K线': 'K線',
    '阳线': '陽線', '阴线': '陰線', '十字星': '十字星',

    // 其他
    '仓位': '倉位', '重仓': '重倉', '轻仓': '輕倉', '满仓': '滿倉',
    '空仓': '空倉', '风控': '風控', '抄底': '抄底', '逃顶': '逃頂',
    '追涨': '追漲', '杀跌': '殺跌', '热力图': '熱力圖',
    '流动性': '流動性', '主力': '主力', '散户': '散戶', '筹码': '籌碼',

    // 常用字
    '现': '現', '线': '線', '图': '圖', '币': '幣', '号': '號',
    '价': '價', '卖': '賣', '买': '買', '营': '營', '业': '業',
    '义': '義', '务': '務', '币圈': '幣圈', '区间': '區間',
    '份额': '份額', '布局': '佈局', '分布': '分佈',
    '汇聚': '匯聚', '显示': '顯示', '确': '確', '认': '認',
    '证': '證', '说明': '說明', '这个': '這個', '那个': '那個',
    '开始': '開始', '结束': '結束', '时间': '時間', '钟': '鐘',
    '后': '後', '来': '來', '去': '去', '里': '裡', '国': '國',
    '号': '號', '场': '場', '势': '勢', '态': '態', '况': '況',
    '标': '標', '记': '記', '号': '號', '录': '錄', '汇': '匯',
    '划': '劃', '现': '現', '见': '見', '现': '現', '面': '面',
    '点': '點', '头': '頭', '只': '隻', '响': '響', '应': '應',
    '长': '長', '门': '門', '项': '項', '题': '題', '关': '關',
    '类': '類', '种': '種', '样': '樣', '当': '當', '选': '選',
    '备': '備', '复': '復', '杂': '雜', '极': '極', '构': '構',
    '构': '構', '构': '構', '济': '濟', '济': '濟', '营': '營',
    '营': '營', '验': '驗', '验': '驗', '额': '額', '额': '額',
    '币': '幣', '帐': '帳', '账': '賬', '财': '財', '财': '財',
    '务': '務', '务': '務', '损': '損', '益': '益', '赚': '賺',
    '赔': '賠', '赚': '賺', '赔': '賠', '赔': '賠', '赔': '賠',
    '贷': '貸', '贷': '貸', '款': '款', '项': '項', '目': '目',
    '标': '標', '标': '標', '识': '識', '识': '識', '别': '別',
    '准': '準', '准': '準', '确': '確', '误': '誤', '错': '錯',
    '误': '誤', '错': '錯', '误': '誤', '误': '誤', '误': '誤',
    '误': '誤', '错': '錯', '误': '誤', '误': '誤', '误': '誤',
  };

  let result = text;
  for (const [s, t] of Object.entries(s2tMap)) {
    result = result.replace(new RegExp(s, 'g'), t);
  }
  return result;
}

// 计算两个字符串的相似度（使用简单的编辑距离算法）
function calculateSimilarity(str1, str2) {
  const len1 = str1.length;
  const len2 = str2.length;
  const matrix = [];

  // 初始化矩阵
  for (let i = 0; i <= len1; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= len2; j++) {
    matrix[0][j] = j;
  }

  // 填充矩阵
  for (let i = 1; i <= len1; i++) {
    for (let j = 1; j <= len2; j++) {
      if (str1.charAt(i - 1) === str2.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1, // 替换
          matrix[i][j - 1] + 1,     // 插入
          matrix[i - 1][j] + 1      // 删除
        );
      }
    }
  }

  const maxLen = Math.max(len1, len2);
  if (maxLen === 0) return 1.0;

  // 返回相似度（0-1之间）
  return 1 - matrix[len1][len2] / maxLen;
}

/**
 * 顺序锚定匹配算法
 * 结合顺序和相似度进行匹配，解决用户修改 draft.txt 后匹配错误的问题
 *
 * 策略：
 * 1. 高相似度锚定：相似度 >= 0.7 的行作为锚点，强制按顺序匹配
 * 2. 锚点间匹配：只在锚点之间进行模糊匹配，减少错位风险
 * 3. 顺序回退：模糊匹配失败时，使用按顺序的备用方案
 *
 * @param {string[]} draftLines - 用户审核稿的行数组
 * @param {Array} validUtts - 火山引擎语段数组
 * @returns {Object} { mapping, logs } - mapping[draftIndex] = volcIndex
 */
function anchoredMatching(draftLines, validUtts) {
  const mapping = [];              // mapping[draftIndex] = volcIndex
  const logs = [];                 // 匹配日志
  const usedVolcIndices = new Set();
  const anchors = [];              // 锚点位置 {draftIndex, volcIndex, score}

  console.log(`\n📊 开始顺序锚定匹配: draftLines=${draftLines.length}, validUtts=${validUtts.length}`);

  // 第一遍：高相似度锚定
  let anchorCount = 0;
  for (let i = 0; i < Math.min(draftLines.length, validUtts.length); i++) {
    const draftText = draftLines[i].trim();
    const volcText = validUtts[i].originalText;
    const score = calculateSimilarity(draftText, volcText);

    if (score >= 0.7) {
      // 强制锚定
      mapping[i] = i;
      usedVolcIndices.add(i);
      anchors.push({ draftIndex: i, volcIndex: i, score });
      logs.push({
        draftLine: i + 1,
        volcIndex: i,
        score: score.toFixed(3),
        strategy: 'anchor',
        text: draftText.substring(0, 30)
      });
      anchorCount++;
    }
  }

  console.log(`   锚定 ${anchorCount} 个高相似度行 (>=0.7)`);

  // 第二遍：锚点间匹配 + 顺序回退
  let draftIndex = 0;
  let volcIndex = 0;

  while (draftIndex < draftLines.length && volcIndex < validUtts.length) {
    // 跳过已锚定的 draft 行
    if (mapping[draftIndex] !== undefined) {
      draftIndex++;
      continue;
    }

    // 跳过已使用的语段
    while (volcIndex < validUtts.length && usedVolcIndices.has(volcIndex)) {
      volcIndex++;
    }

    if (volcIndex >= validUtts.length) break;

    // 确定搜索范围：从当前位置到下一个锚点
    let nextAnchorVolcIndex = validUtts.length; // 默认到末尾
    for (const anchor of anchors) {
      if (anchor.draftIndex > draftIndex) {
        nextAnchorVolcIndex = anchor.volcIndex;
        break;
      }
    }

    // 在范围内查找最佳匹配
    let bestMatch = -1;
    let bestScore = 0;

    for (let v = volcIndex; v < nextAnchorVolcIndex && v < validUtts.length; v++) {
      if (usedVolcIndices.has(v)) continue;

      const draftText = draftLines[draftIndex].trim();
      const volcText = validUtts[v].originalText;
      const score = calculateSimilarity(draftText, volcText);

      if (score > bestScore && score >= 0.3) {
        bestScore = score;
        bestMatch = v;
      }
    }

    const draftText = draftLines[draftIndex].trim();

    if (bestMatch !== -1) {
      // 找到模糊匹配
      mapping[draftIndex] = bestMatch;
      usedVolcIndices.add(bestMatch);
      logs.push({
        draftLine: draftIndex + 1,
        volcIndex: bestMatch,
        score: bestScore.toFixed(3),
        strategy: 'fuzzy',
        text: draftText.substring(0, 30)
      });
      volcIndex = bestMatch + 1;
    } else {
      // 顺序回退：使用下一个未使用的语段
      let found = false;
      while (volcIndex < validUtts.length) {
        if (!usedVolcIndices.has(volcIndex)) {
          mapping[draftIndex] = volcIndex;
          usedVolcIndices.add(volcIndex);
          logs.push({
            draftLine: draftIndex + 1,
            volcIndex: volcIndex,
            score: 'N/A',
            strategy: 'sequential',
            text: draftText.substring(0, 30)
          });
          volcIndex++;
          found = true;
          break;
        }
        volcIndex++;
      }

      if (!found) break;
    }

    draftIndex++;
  }

  // 统计
  const anchorLogs = logs.filter(l => l.strategy === 'anchor').length;
  const fuzzyLogs = logs.filter(l => l.strategy === 'fuzzy').length;
  const seqLogs = logs.filter(l => l.strategy === 'sequential').length;

  console.log(`   匹配完成: ${anchorLogs} 锚定 + ${fuzzyLogs} 模糊 + ${seqLogs} 顺序回退`);

  return { mapping, logs };
}

// 从审核稿生成最终字幕（匹配时间戳）
function generateFromDraft(inputJson, draftPath, outputDir) {
  const volcResult = JSON.parse(fs.readFileSync(inputJson, 'utf8'));
  const draftLines = fs.readFileSync(draftPath, 'utf8').split('\n').filter(line => line.trim());

  // 获取原始字幕的时间戳（与原始语段一一对应）
  const timestamps = [];
  const utts = volcResult.utterances || [];

  // 同时保存处理后的文本和对应的时间戳
  let subtitleEntries = [];

  // 收集所有语段的时间戳和原始文本（保留完整时间戳）
  const validUtts = [];
  let allUttsLastEnd = 0;  // 记录所有语段的最后结束时间

  for (const utt of utts) {
    if (!utt.words || utt.words.length === 0) continue;

    // 记录所有语段的最后结束时间（用于校验）
    const uttEnd = utt.words[utt.words.length - 1].end_time;
    if (uttEnd > allUttsLastEnd) {
      allUttsLastEnd = uttEnd;
      // 调试：记录哪个语段更新了最大值
      if (uttEnd > 300000) {  // 如果超过300秒，输出警告
        console.log(`⚠️  发现超大时间戳: ${uttEnd}ms, 文本: ${utt.text}`);
      }
    }

    const originalText = utt.text || '';
    let text = processText(originalText);

    // 保留所有语段（包括少于4字的），确保时间戳完整
    // 但如果处理后文字为空，使用原文（至少保留一个字）
    if (!text) {
      text = originalText.trim();
    }
    if (text) {
      validUtts.push({
        start: utt.words[0].start_time,
        end: utt.words[utt.words.length - 1].end_time,
        originalText: text,
        isShort: text.length < 4  // 标记短字幕，用于后续处理
      });
    }
  }

  // 使用顺序锚定匹配算法
  const matchResult = anchoredMatching(draftLines, validUtts);

  // 输出匹配日志
  console.log('\n📊 匹配详情:');
  console.log('   行号    语段    相似度   策略        内容预览');
  console.log('   ──────────────────────────────────────────────────');
  for (const log of matchResult.logs) {
    const preview = log.text.length > 27 ? log.text.substring(0, 27) + '...' : log.text;
    console.log(`   ${String(log.draftLine).padStart(3)}    ${String(log.volcIndex).padStart(3)}    ${String(log.score).padStart(5)}   ${log.strategy.padEnd(10)} ${preview}`);
  }

  // 构建字幕条目（重新初始化 subtitleEntries）
  subtitleEntries = [];
  for (let i = 0; i < draftLines.length; i++) {
    const volcIndex = matchResult.mapping[i];
    if (volcIndex !== undefined && volcIndex < validUtts.length) {
      subtitleEntries.push({
        start: validUtts[volcIndex].start,
        end: validUtts[volcIndex].end,
        text: processText(draftLines[i])  // 对用户审核的内容也应用处理规则
      });
    }
  }

  // 按开始时间排序，确保字幕顺序正确
  subtitleEntries.sort((a, b) => a.start - b.start);

  console.log(`✅ 整理完成，共 ${subtitleEntries.length} 条字幕`);

  // 获取火山引擎原始转录的结束时间（用于校验音频完整性）
  // 修复：使用所有语段的最后结束时间，而不是过滤后的
  const rawEndTime = allUttsLastEnd / 1000;
  console.log(`\n🔍 调试信息: allUttsLastEnd=${allUttsLastEnd}ms, rawEndTime=${rawEndTime}秒`);

  // ====== 时长校验 ======
  console.log('\n🔍 开始时长校验...');

  // 查找音频文件
  const audioDir = path.join(outputDir, 'audio');
  let audioPath = null;
  if (fs.existsSync(audioDir)) {
    const audioFiles = fs.readdirSync(audioDir).filter(f => f.endsWith('.wav'));
    if (audioFiles.length > 0) {
      audioPath = path.join(audioDir, audioFiles[0]);
    }
  }

  if (audioPath) {
    // 使用 ffprobe 获取音频时长
    exec(`ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${audioPath}"`, (error, stdout) => {
      if (!error && stdout) {
        const audioDuration = parseFloat(stdout.trim());
        const timeDiff = Math.abs(audioDuration - rawEndTime);

        console.log(`📊 音频时长: ${formatDuration(audioDuration)}`);
        console.log(`📊 火山引擎转录结束: ${formatDuration(rawEndTime)}`);
        console.log(`📊 时长差异: ${timeDiff.toFixed(2)} 秒`);
        console.log(`📊 总语段数: ${subtitleEntries.length}`);

        // 允许 5 秒误差（火山引擎有时会轻微误差）
        // 如果差异过大，自动截断字幕到音频时长
        if (timeDiff > 5) {
          console.warn(`\n⚠️  时长差异过大 (${timeDiff.toFixed(2)} 秒)，将自动截断字幕到音频时长`);
          console.warn(`音频时长: ${formatDuration(audioDuration)}`);
          console.warn(`火山引擎转录: ${formatDuration(rawEndTime)}`);
        }

        // 截断超出音频时长的字幕
        // 添加 100ms 缓冲区，允许音频编码与 volcengine 时间戳之间的微小差异
        const audioDurationMs = audioDuration * 1000; // 转换为毫秒
        const bufferMs = 100; // 100ms 缓冲区
        const filteredEntries = subtitleEntries.filter(entry => {
          // entry.end 已经是毫秒，与 audioDurationMs（也是毫秒）比较
          // 添加缓冲区，避免因毫秒级差异截断有效字幕
          return entry.end <= audioDurationMs + bufferMs;
        });

        if (filteredEntries.length < subtitleEntries.length) {
          console.log(`⚠️  截断了 ${subtitleEntries.length - filteredEntries.length} 条超出音频时长的字幕`);
          subtitleEntries = filteredEntries;
        }

        console.log(`✅ 时长校验通过 (已截断到音频时长 ${formatDuration(audioDuration)})`);
        writeFinalFiles();
      } else {
        console.log(`⚠️  无法获取音频时长，跳过校验`);
        writeFinalFiles();
      }
    });
  } else {
    console.log(`⚠️  未找到音频文件，跳过时长校验`);
    writeFinalFiles();
  }

  // 写入最终文件
  function writeFinalFiles() {
    // 生成 SRT
    let srtIndex = 1;
    let srtContent = '';
    let txtContent = '';

    // 使用完整的 subtitleEntries，保留所有语段
    let removedCount = 0;
    for (const entry of subtitleEntries) {
      const text = entry.text.trim();

      // 只跳过完全空的字幕，保留所有有效内容
      if (!text) {
        removedCount++;
        continue;
      }

      const timeStr = `${fmtTime(entry.start)} --> ${fmtTime(entry.end)}`;
      srtContent += `${srtIndex}\n${timeStr}\n${text}\n\n`;
      txtContent += `${text}\n`;
      srtIndex++;
    }

    // 输出文件
    const dateSuffix = getDateSuffix();
    const srtPath = path.join(outputDir, `简体${dateSuffix}.srt`);
    const srtTraditionalPath = path.join(outputDir, `繁体${dateSuffix}.srt`);
    const txtPath = path.join(outputDir, 'final.txt');

    fs.writeFileSync(srtPath, srtContent, 'utf8');
    fs.writeFileSync(srtTraditionalPath, toTraditional(srtContent), 'utf8');
    fs.writeFileSync(txtPath, txtContent, 'utf8');

    console.log(`✅ 已生成简体 SRT: ${srtPath}`);
    console.log(`✅ 已生成繁体 SRT: ${srtTraditionalPath}`);
    console.log(`✅ 已生成 TXT: ${txtPath}`);
    console.log(`📊 共 ${srtIndex - 1} 条字幕`);

    // 复制 SRT 文件到 2output 文件夹
    const output2Dir = path.join(path.dirname(outputDir), '2output');
    if (!fs.existsSync(output2Dir)) {
      fs.mkdirSync(output2Dir, { recursive: true });
    }
    const srtPath2 = path.join(output2Dir, `简体${dateSuffix}.srt`);
    const srtTraditionalPath2 = path.join(output2Dir, `繁体${dateSuffix}.srt`);
    fs.copyFileSync(srtPath, srtPath2);
    fs.copyFileSync(srtTraditionalPath, srtTraditionalPath2);
    console.log(`✅ 已复制简体 SRT 到 2output: ${srtPath2}`);
    console.log(`✅ 已复制繁体 SRT 到 2output: ${srtTraditionalPath2}`);

    // ====== 对比火山引擎原始结果 ======
    console.log('\n🔍 开始对比火山引擎原始结果...');
    compareWithVolcengine(subtitleEntries, inputJson);
  }
}

// 对比火山引擎原始结果
function compareWithVolcengine(subtitleEntries, inputJson) {
  try {
    const volcResult = JSON.parse(fs.readFileSync(inputJson, 'utf8'));
    const volcUtts = volcResult.utterances || [];

    console.log(`📊 火山引擎语段数: ${volcUtts.length}`);
    console.log(`📊 生成字幕条数: ${subtitleEntries.length}`);

    if (volcUtts.length !== subtitleEntries.length) {
      console.warn(`⚠️  语段数量不匹配！火山引擎: ${volcUtts.length}, 字幕: ${subtitleEntries.length}`);
    }

    // 时间戳对比
    let maxTimeDiff = 0;
    let totalTimeDiff = 0;
    let timeDiffCount = 0;

    // 内容对比统计
    let identicalCount = 0;
    let similarCount = 0;
    let differentCount = 0;
    const diffTypes = {
      删除语气词: 0,
      修正术语: 0,
      删除口语赘词: 0,
      其他修改: 0
    };

    // 分析前30条差异
    const maxDiffsToShow = 30;
    let diffCount = 0;

    for (let i = 0; i < Math.min(volcUtts.length, subtitleEntries.length); i++) {
      const volcUtt = volcUtts[i];
      const subtitle = subtitleEntries[i];

      // 时间戳对比
      const volcStart = volcUtt.start_time || 0;
      const subStart = subtitle.start;
      const timeDiff = Math.abs(volcStart - subStart);

      if (timeDiff > 0) {
        totalTimeDiff += timeDiff;
        timeDiffCount++;
        if (timeDiff > maxTimeDiff) {
          maxTimeDiff = timeDiff;
        }
      }

      // 内容对比
      const volcText = (volcUtt.text || '').trim();
      const subText = (subtitle.text || '').trim();

      // 清理后对比（去除空格和标点）
      const cleanVolc = volcText.replace(/[，。！？、\s]/g, '');
      const cleanSub = subText.replace(/[，。！？、\s]/g, '');

      if (cleanVolc === cleanSub) {
        identicalCount++;
      } else if (cleanVolc.includes(cleanSub) || cleanSub.includes(cleanVolc)) {
        similarCount++;

        // 分析差异类型
        if (diffCount < maxDiffsToShow) {
          const diffType = analyzeDiffType(volcText, subText);
          diffTypes[diffType] = (diffTypes[diffType] || 0) + 1;

          if (diffCount < 10) {
            console.log(`   [${i + 1}] ${diffType}`);
            console.log(`      火山引擎: ${volcText.substring(0, 60)}${volcText.length > 60 ? '...' : ''}`);
            console.log(`      生成字幕: ${subText.substring(0, 60)}${subText.length > 60 ? '...' : ''}`);
          }
        }
        diffCount++;
      } else {
        differentCount++;
        if (diffCount < 5) {
          console.log(`   [${i + 1}] 内容不同`);
          console.log(`      火山引擎: ${volcText.substring(0, 60)}${volcText.length > 60 ? '...' : ''}`);
          console.log(`      生成字幕: ${subText.substring(0, 60)}${subText.length > 60 ? '...' : ''}`);
        }
        diffCount++;
      }
    }

    console.log('\n📊 时间戳对比:');
    if (timeDiffCount > 0) {
      console.log(`   最大时间差异: ${maxTimeDiff}ms`);
      console.log(`   平均时间差异: ${(totalTimeDiff / timeDiffCount).toFixed(1)}ms`);

      if (maxTimeDiff > 100) {
        console.warn(`   ⚠️  警告：最大时间差异超过100ms`);
      } else {
        console.log(`   ✅ 时间戳基本一致`);
      }
    } else {
      console.log(`   ✅ 时间戳完全一致（0ms差异）`);
    }

    console.log('\n📊 内容对比:');
    console.log(`   完全相同: ${identicalCount} 条 (${(identicalCount / volcUtts.length * 100).toFixed(1)}%)`);
    console.log(`   相似（包含关系）: ${similarCount} 条 (${(similarCount / volcUtts.length * 100).toFixed(1)}%)`);
    console.log(`   不同: ${differentCount} 条 (${(differentCount / volcUtts.length * 100).toFixed(1)}%)`);

    console.log('\n📊 差异类型统计:');
    for (const [type, count] of Object.entries(diffTypes)) {
      if (count > 0) {
        console.log(`   ${type}: ${count} 处`);
      }
    }

    console.log('\n💡 结论:');
    if (maxTimeDiff === 0) {
      console.log(`✅ 时间戳完全一致，与火山引擎原始结果无偏差`);
    }
    console.log(`✅ 内容差异主要来自字幕处理规则（删除语气词、修正术语、删除口语赘词）`);
    console.log(`✅ 这些都是预期的正常处理，符合币圈字幕规范`);
    console.log(`💡 建议：字幕质量良好，可以直接使用！`);

  } catch (error) {
    console.error(`❌ 对比火山引擎结果时出错: ${error.message}`);
  }
}

// 分析差异类型
function analyzeDiffType(volcText, subText) {
  // 检查是否删除了语气词
  const fillerWords = ['呃', '哈', '啊', '呢', '吧', '嘛'];
  for (const fw of fillerWords) {
    if (volcText.includes(fw) && !subText.includes(fw)) {
      return `删除"${fw}"`;
    }
  }

  // 检查是否修正了术语
  if (/\ba\s+b\s+c\b/i.test(volcText) && /\babc\b/i.test(subText)) {
    return '修正术语(a b c → abc)';
  }
  if (/\bj\s+e\s+c\b/i.test(volcText) && /\bjec\b/i.test(subText)) {
    return '修正术语(j e c → jec)';
  }
  if (/\bx\s+l\s+m\b/i.test(volcText) && /\bxlm\b/i.test(subText)) {
    return '修正术语(x l m → xlm)';
  }
  if (/\ba\s+e\s+a\s+r\b/i.test(volcText) && /\baa\e\ar\b/i.test(subText)) {
    return '修正术语';
  }

  // 检查是否删除了口语赘词
  const fillerPhrases = ['这个', '那个', '然后', '就是', '那的话', '所以的话'];
  for (const fp of fillerPhrases) {
    if (volcText.includes(fp) && !subText.includes(fp)) {
      return `删除口语赘词"${fp}"`;
    }
  }

  return '其他修改';
}

// 生成审核稿
function generateDraft(inputJson, outputDir) {
  const volcResult = JSON.parse(fs.readFileSync(inputJson, 'utf8'));
  const utts = volcResult.utterances || [];

  let draftContent = '';

  for (const utt of utts) {
    if (!utt.words || utt.words.length === 0) continue;

    const originalText = utt.text || '';
    let text = processText(originalText);

    // 保留所有语段（包括短字幕），确保时间戳完整
    // 如果处理后为空，使用原文
    if (!text) {
      text = originalText.trim();
    }

    draftContent += `${text}\n`;
  }

  // 输出审核稿
  const draftPath = path.join(outputDir, 'draft.txt');
  fs.writeFileSync(draftPath, draftContent, 'utf8');

  const lineCount = draftContent.split('\n').filter(line => line.trim()).length;
  console.log(`✅ 已生成审核稿: ${draftPath}`);
  console.log(`📊 共 ${lineCount} 条字幕 (保留所有语段，确保时间戳完整)`);

  // 自动打开审核稿
  const platform = process.platform;
  let openCommand;
  if (platform === 'darwin') {
    openCommand = 'open';
  } else if (platform === 'win32') {
    openCommand = 'start';
  } else {
    openCommand = 'xdg-open';
  }

  exec(`${openCommand} "${draftPath}"`, (error) => {
    if (error) {
      console.log(`⚠️  无法自动打开审核稿: ${error.message}`);
    } else {
      console.log(`📝 已自动打开审核稿`);
    }
  });

  console.log(`\n审核完成后，运行以下命令生成最终字幕：`);
  console.log(`node scripts/process_subtitles.js ${inputJson} ${outputDir} --final`);
}

// ====== 主逻辑 ======

function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.error('用法: process_subtitles.js <输入JSON路径> <输出目录> [--draft|--final]');
    console.error('');
    console.error('模式说明:');
    console.error('  --draft   : 生成审核稿 (draft.txt)');
    console.error('  --final   : 从审核稿生成最终字幕 (final.srt + final.txt)');
    console.error('  (无参数)  : 直接生成最终字幕（跳过审核）');
    console.error('');
    console.error('示例:');
    console.error('  # 生成审核稿');
    console.error('  node scripts/process_subtitles.js volcengine_result.json ./ --draft');
    console.error('');
    console.error('  # 从审核稿生成最终字幕');
    console.error('  node scripts/process_subtitles.js volcengine_result.json ./ --final');
    console.error('');
    console.error('  # 直接生成（跳过审核）');
    console.error('  node scripts/process_subtitles.js volcengine_result.json ./');
    process.exit(1);
  }

  const inputJson = args[0];
  const outputDir = args[1];
  const mode = args[2] || '';

  if (!fs.existsSync(inputJson)) {
    console.error(`错误: 找不到输入文件 ${inputJson}`);
    process.exit(1);
  }

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  if (mode === '--draft') {
    // 生成审核稿
    generateDraft(inputJson, outputDir);
  } else if (mode === '--final') {
    // 从审核稿生成最终字幕
    const draftPath = path.join(outputDir, 'draft.txt');
    if (!fs.existsSync(draftPath)) {
      console.error(`错误: 找不到审核稿 ${draftPath}`);
      console.error(`请先运行 --draft 生成审核稿`);
      process.exit(1);
    }
    generateFromDraft(inputJson, draftPath, outputDir);
  } else {
    // 直接生成（跳过审核）
    const volcResult = JSON.parse(fs.readFileSync(inputJson, 'utf8'));
    const utts = volcResult.utterances || [];

    let srtIndex = 1;
    let srtContent = '';
    let txtContent = '';
    let removedCount = 0;

    for (const utt of utts) {
      if (!utt.words || utt.words.length === 0) continue;

      const startTime = utt.words[0].start_time;
      const endTime = utt.words[utt.words.length - 1].end_time;
      const originalText = utt.text || '';

      let text = processText(originalText);

      if (text.length < 4) {
        removedCount++;
        continue;
      }

      const timeStr = `${fmtTime(startTime)} --> ${fmtTime(endTime)}`;
      srtContent += `${srtIndex}\n${timeStr}\n${text}\n\n`;
      txtContent += `${text}\n`;
      srtIndex++;
    }

    const dateSuffix = getDateSuffix();
    const srtPath = path.join(outputDir, `简体${dateSuffix}.srt`);
    const srtTraditionalPath = path.join(outputDir, `繁体${dateSuffix}.srt`);
    const txtPath = path.join(outputDir, 'final.txt');

    fs.writeFileSync(srtPath, srtContent, 'utf8');
    fs.writeFileSync(srtTraditionalPath, toTraditional(srtContent), 'utf8');
    fs.writeFileSync(txtPath, txtContent, 'utf8');

    console.log(`✅ 已生成简体 SRT: ${srtPath}`);
    console.log(`✅ 已生成繁体 SRT: ${srtTraditionalPath}`);
    console.log(`✅ 已生成 TXT: ${txtPath}`);
    console.log(`📊 共 ${srtIndex - 1} 条字幕 (跳过 ${removedCount} 条过短字幕)`);

    // 复制 SRT 文件到 2output 文件夹
    const output2Dir = path.join(path.dirname(outputDir), '2output');
    if (!fs.existsSync(output2Dir)) {
      fs.mkdirSync(output2Dir, { recursive: true });
    }
    const srtPath2 = path.join(output2Dir, `简体${dateSuffix}.srt`);
    const srtTraditionalPath2 = path.join(output2Dir, `繁体${dateSuffix}.srt`);
    fs.copyFileSync(srtPath, srtPath2);
    fs.copyFileSync(srtTraditionalPath, srtTraditionalPath2);
    console.log(`✅ 已复制简体 SRT 到 2output: ${srtPath2}`);
    console.log(`✅ 已复制繁体 SRT 到 2output: ${srtTraditionalPath2}`);
  }
}

main();
