'''实现agent工具类'''
'''rag_summarize,list_majors,assess_risk,generate_report'''
import re
import os
from datetime import datetime
from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
from utils.path_tool import get_abs_path

rag = RagSummarizeService()

# 文件缓存：{relative_path: (mtime, content)}
_file_cache: dict[str, tuple[float, str]] = {}


def _read_data_file(relative_path: str) -> str:
    '''读取数据文件，带修改时间检测的缓存'''
    abs_path = get_abs_path(relative_path)
    try:
        mtime = os.path.getmtime(abs_path)
    except OSError:
        return f"[错误] 数据文件不存在: {relative_path}"

    cached = _file_cache.get(relative_path)
    if cached and cached[0] == mtime:
        return cached[1]

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        _file_cache[relative_path] = (mtime, content)
        return content
    except Exception as e:
        return f"[错误] 读取数据文件失败: {str(e)}"


@tool(description="从向量存储中检索参考资料")
def rag_summarize(query: str) -> str:
    '''RAG总结工具'''
    return rag.rag_summarize(query)




@tool(description="查看张雪峰推荐和不推荐的专业列表，可按家庭类型筛选")
def list_majors(family_type: str = "普通家庭") -> str:
    '''专业推荐列表工具，按家庭类型展示推荐和不推荐的专业'''
    content = _read_data_file("data/04专业选择分析汇总.txt")
    if content.startswith("[错误]"):
        return content

    # 解析推荐专业
    recommended = []
    rec_match = re.search(r'一、张雪峰推荐的专业\s*\n(.*?)(?=\n## 二、)', content, re.DOTALL)
    if rec_match:
        rec_text = rec_match.group(1)
        majors = re.split(r'\n### （[一二三四五六七八九十]+）', rec_text)
        for i, major_block in enumerate(majors):
            # 第一块包含第一个 ### 标头，清理掉
            if i == 0:
                major_block = re.sub(r'^.*?### （[一二三四五六七八九十]+）\s*\n', '\n', major_block, count=1, flags=re.DOTALL)
            lines = major_block.strip().split('\n')
            major_name = lines[0].strip() if lines else "未知专业"
            major_name = re.sub(r'^### （[一二三四五六七八九十]+）\s*', '', major_name)
            # 提取推荐理由
            reason = ""
            reason_match = re.search(r'\*\*推荐理由[：:]\*\*\s*\n(.*?)(?=\n\*\*|\n###|\Z)', major_block, re.DOTALL)
            if reason_match:
                reason = reason_match.group(1).strip()
                # 清理 markdown 格式
                reason = re.sub(r'^\d+\.\s*', '', reason, flags=re.MULTILINE)
                reason = reason.replace('- ', '').replace('**', '')
                reason = '\n'.join(line.strip() for line in reason.split('\n') if line.strip())
            # 提取注意事项
            notes = ""
            notes_match = re.search(r'\*\*(?:注意事项|特殊提醒|补充说明|风险提示)[：:]\*\*\s*\n(.*?)(?=\n\*\*|\n###|\Z)', major_block, re.DOTALL)
            if notes_match:
                notes = notes_match.group(1).strip()
                notes = notes.replace('- ', '').replace('**', '')
                notes = '\n'.join(line.strip() for line in notes.split('\n') if line.strip())
            recommended.append((major_name, reason, notes))

    # 解析不推荐专业
    not_recommended = []
    not_rec_match = re.search(r'二、张雪峰不推荐/慎报的专业\s*\n(.*?)(?=\n## 三、)', content, re.DOTALL)
    if not_rec_match:
        not_rec_text = not_rec_match.group(1)
        majors = re.split(r'\n### （[一二三四五六七八九十]+）', not_rec_text)
        for i, major_block in enumerate(majors):
            if i == 0:
                major_block = re.sub(r'^.*?### （[一二三四五六七八九十]+）\s*\n', '\n', major_block, count=1, flags=re.DOTALL)
            lines = major_block.strip().split('\n')
            major_name = lines[0].strip() if lines else "未知专业"
            major_name = re.sub(r'^### （[一二三四五六七八九十]+）\s*', '', major_name)
            reason = ""
            reason_match = re.search(r'\*\*不推荐理由[：:]\*\*\s*\n(.*?)(?=\n\*\*|\n###|\Z)', major_block, re.DOTALL)
            if reason_match:
                reason = reason_match.group(1).strip()
                reason = re.sub(r'^\d+\.\s*', '', reason, flags=re.MULTILINE)
                reason = reason.replace('- ', '').replace('**', '')
                reason = '\n'.join(line.strip() for line in reason.split('\n') if line.strip())
            # 提取例外/补充
            exception = ""
            exc_match = re.search(r'\*\*(?:例外情况|特殊提醒|补充说明)[：:]\*\*\s*\n(.*?)(?=\n\*\*|\n###|\Z)', major_block, re.DOTALL)
            if exc_match:
                exception = exc_match.group(1).strip()
                exception = exception.replace('- ', '').replace('**', '')
                exception = '\n'.join(line.strip() for line in exception.split('\n') if line.strip())
            not_recommended.append((major_name, reason, exception))

    # 格式化输出
    output = f"=== 张雪峰推荐专业（家庭类型：{family_type}）===\n\n"
    for i, (name, reason, notes) in enumerate(recommended, 1):
        output += f"{i}. {name}\n"
        if reason:
            # 截取前100字避免过长
            reason_brief = reason[:100] + "..." if len(reason) > 100 else reason
            output += f"   推荐理由：{reason_brief}\n"
        if notes:
            notes_brief = notes[:60] + "..." if len(notes) > 60 else notes
            output += f"   注意：{notes_brief}\n"
        output += "\n"

    output += f"=== 张雪峰不推荐/慎报专业 ===\n\n"
    for i, (name, reason, exception) in enumerate(not_recommended, 1):
        output += f"{i}. {name}\n"
        if reason:
            reason_brief = reason[:100] + "..." if len(reason) > 100 else reason
            output += f"   不推荐理由：{reason_brief}\n"
        if exception:
            exception_brief = exception[:60] + "..." if len(exception) > 60 else exception
            output += f"   例外：{exception_brief}\n"
        output += "\n"

    return output.strip()




@tool(description="根据位次和志愿方案，评估填报风险并给出建议。schools格式：每行一个'学校|专业1,专业2|预估位次'")
def assess_risk(
    rank: int,
    schools: str,
    accept_adjustment: bool = True,
    priority: str = "专业优先",
    weak_subjects: str = ""
) -> str:
    '''志愿风险评估工具，基于张雪峰填报方法论规则进行风险诊断'''

    # 弱势科目与相关专业映射
    SUBJECT_MAJOR_MAP = {
        "物理": ["电子信息", "通信", "自动化", "机械", "土木", "电气", "物理", "力学", "光学", "材料"],
        "化学": ["化学", "化工", "制药", "材料", "环境", "生物工程", "医学", "临床"],
        "数学": ["数学", "统计", "金融", "会计", "经济学", "计算机科学"],
        "历史": ["历史", "考古", "哲学"],
    }

    # 天坑专业（不推荐普通家庭）
    BLACKLIST_MAJOR = ["新闻", "工商管理", "市场营销", "石油", "英语", "生化环材", "护理", "农学"]

    def parse_schools(text: str) -> list[dict]:
        result = []
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.split('|')
            if len(parts) < 3:
                continue
            name = parts[0].strip()
            majors = [m.strip() for m in parts[1].split(',') if m.strip()]
            try:
                school_rank = int(parts[2].strip())
            except ValueError:
                continue
            result.append({"name": name, "majors": majors, "rank": school_rank})
        return result

    def check_gradient(entries: list[dict], student_rank: int) -> tuple[str, list[str]]:
        chong, wen, bao = [], [], []
        for e in entries:
            diff = e["rank"] - student_rank
            if diff < -3000:
                chong.append(e)
            elif diff > 3000:
                bao.append(e)
            else:
                wen.append(e)

        issues = []
        if not chong:
            issues.append("缺少冲的志愿，建议增加1-2个目标位次略高于自身的学校")
        if not wen:
            issues.append("缺少稳的志愿，建议增加1-2个位次接近的学校")
        if not bao:
            issues.append("缺少保的志愿，强烈建议增加2-3个位次明显低于自身的学校作为保底")
        elif len(bao) < 2:
            issues.append(f"保底志愿仅{len(bao)}个，建议增加到2-3个")

        tag = "梯度合理" if not issues else "梯度不均"
        return tag, issues, len(chong), len(wen), len(bao)

    def check_slide_risk(entries: list[dict]) -> tuple[str, list[str]]:
        if len(entries) < 2:
            return "信息不足", ["志愿数量过少，无法评估滑档风险"]
        ranks = [e["rank"] for e in entries]
        spread = max(ranks) - min(ranks)
        issues = []
        if spread < 5000:
            issues.append(f"志愿间最大位次差仅{spread}，过于扁平，建议拉开到5000以上")
        if spread < 3000:
            issues.append("志愿几乎在同一分数段，滑档风险极高！670分状元也可能滑档")
        tag = "滑档风险低" if spread >= 8000 else ("滑档风险中" if spread >= 5000 else "滑档风险高")
        return tag, issues

    def check_adjustment(entries: list[dict], accept_adj: bool, prio: str) -> tuple[str, list[str]]:
        issues = []
        if not accept_adj:
            chong_count = sum(1 for e in entries if e["rank"] < entries[0]["rank"] - 3000)
            if chong_count > 0:
                issues.append(f"不服从调剂且有{chong_count}个冲的志愿，被退档后只能参加补录或下一批次")
            if prio == "专业优先":
                issues.append("专业优先策略下不服从调剂，一旦所选专业满额将直接退档")
            tag = "调剂风险高" if issues else "调剂策略需关注"
        else:
            tag = "调剂策略合理"
        return tag, issues

    def check_subject_major(weak: str, entries: list[dict]) -> tuple[str, list[str]]:
        if not weak.strip():
            return "无弱势科目", []
        weak_list = [s.strip() for s in weak.split(',') if s.strip()]
        issues = []
        for e in entries:
            for major in e["majors"]:
                for subj, related in SUBJECT_MAJOR_MAP.items():
                    if subj in weak_list:
                        for r in related:
                            if r in major:
                                issues.append(f"{e['name']}的{major}要求{subj}基础，但{subj}为弱势科目，建议慎报")
                                break
        tag = "科目匹配" if not issues else "科目冲突"
        return tag, issues

    def check_strategy_consistency(prio: str, accept_adj: bool) -> tuple[str, list[str]]:
        issues = []
        if prio == "学校优先" and not accept_adj:
            issues.append("学校优先+不服从调剂=极高风险，要么接受调剂要么做好退档准备")
        if prio == "专业优先" and not accept_adj:
            issues.append("专业优先但不服从调剂，建议重新考虑是否服从调剂以降低退档风险")
        tag = "策略一致" if not issues else "策略矛盾"
        return tag, issues

    def check_blacklist(entries: list[dict]) -> list[str]:
        issues = []
        for e in entries:
            for major in e["majors"]:
                for bl in BLACKLIST_MAJOR:
                    if bl in major:
                        issues.append(f"{e['name']}的{major}属于不推荐专业（天坑），普通家庭慎报")
                        break
        return issues

    # === 主逻辑 ===
    entries = parse_schools(schools)
    if not entries:
        return "[错误] 未解析到有效志愿方案，请检查格式：每行 '学校|专业1,专业2|预估位次'"

    # 按位次排序（从小到大，即冲→稳→保）
    entries.sort(key=lambda x: x["rank"])

    # 执行5项检查
    grad_tag, grad_issues, n_chong, n_wen, n_bao = check_gradient(entries, rank)
    slide_tag, slide_issues = check_slide_risk(entries)
    adj_tag, adj_issues = check_adjustment(entries, accept_adjustment, priority)
    subj_tag, subj_issues = check_subject_major(weak_subjects, entries)
    strat_tag, strat_issues = check_strategy_consistency(priority, accept_adjustment)
    bl_issues = check_blacklist(entries)

    all_issues = grad_issues + slide_issues + adj_issues + subj_issues + strat_issues + bl_issues
    error_count = sum(1 for tag in [grad_tag, slide_tag, adj_tag, subj_tag, strat_tag]
                      if "高" in tag or "矛盾" in tag or "冲突" in tag)
    warn_count = len(all_issues) - error_count

    if error_count >= 2:
        risk_level = "高风险"
    elif error_count >= 1 or warn_count >= 3:
        risk_level = "中风险"
    else:
        risk_level = "低风险"

    # 格式化输出
    lines = []
    lines.append("=== 志愿风险评估报告 ===\n")
    lines.append(f"考生位次：{rank}")
    lines.append(f"志愿数量：{len(entries)}个")
    lines.append(f"填报策略：{priority}")
    lines.append(f"服从调剂：{'是' if accept_adjustment else '否'}")
    if weak_subjects:
        lines.append(f"弱势科目：{weak_subjects}")
    lines.append("")

    lines.append(f"【风险等级】{risk_level}\n")
    lines.append("【诊断结果】")

    idx = 1
    # 梯度
    icon = "✅" if not grad_issues else "⚠️"
    lines.append(f"{idx}. {icon} 梯度：冲{n_chong}个 稳{n_wen}个 保{n_bao}个 — {grad_tag}")
    for issue in grad_issues:
        lines.append(f"   → {issue}")
    idx += 1

    # 滑档
    icon = "✅" if not slide_issues else ("❌" if "极高" in str(slide_issues) else "⚠️")
    lines.append(f"{idx}. {icon} 滑档：{slide_tag}")
    for issue in slide_issues:
        lines.append(f"   → {issue}")
    idx += 1

    # 调剂
    icon = "✅" if not adj_issues else ("❌" if "高" in adj_tag else "⚠️")
    lines.append(f"{idx}. {icon} 调剂：{adj_tag}")
    for issue in adj_issues:
        lines.append(f"   → {issue}")
    idx += 1

    # 科目
    icon = "✅" if not subj_issues else "⚠️"
    lines.append(f"{idx}. {icon} 科目：{subj_tag}")
    for issue in subj_issues:
        lines.append(f"   → {issue}")
    idx += 1

    # 策略一致性
    icon = "✅" if not strat_issues else "❌"
    lines.append(f"{idx}. {icon} 策略：{strat_tag}")
    for issue in strat_issues:
        lines.append(f"   → {issue}")
    idx += 1

    # 天坑专业
    if bl_issues:
        lines.append(f"{idx}. ⚠️ 天坑专业提醒")
        for issue in bl_issues:
            lines.append(f"   → {issue}")

    # 具体建议
    suggestions = []
    if n_bao < 2:
        suggestions.append("增加保底志愿到2-3个，位次应在自身位次+5000以上")
    if not accept_adjustment:
        suggestions.append("强烈建议服从调剂，不服从调剂退档后果严重")
    if n_chong > len(entries) * 0.6:
        suggestions.append("冲的志愿占比过高，建议增加稳和保的比例")
    if slide_issues:
        suggestions.append("拉开志愿梯度，五分一个档次，避免志愿扁平")
    if bl_issues:
        suggestions.append("避开天坑专业，选择有专业壁垒的方向")
    if subj_issues:
        suggestions.append("弱势科目相关的专业慎报，选择与自身优势匹配的方向")

    if suggestions:
        lines.append("")
        lines.append("【具体建议】")
        for i, s in enumerate(suggestions, 1):
            lines.append(f"{i}. {s}")

    return '\n'.join(lines)




@tool(description="无入参，无返回值，调用后触发中间件自动为报告生成的场景动态注入上下文信息，为后续提示词切换提供上下文信息")
def fill_context_for_report():
    return "fill_context_for_report已调用"

@tool(description="记录考生高考位次，用于后续生成志愿填报报告")
def set_rank(rank: int) -> str:
    return f"已记录位次：{rank}"

@tool(description="记录考生所在省份，用于后续生成志愿填报报告")
def set_province(province: str) -> str:
    return f"已记录省份：{province}"

@tool(description="记录填报策略偏好，可选值：专业优先、学校优先")
def set_priority(priority: str) -> str:
    return f"已记录填报策略：{priority}"

@tool(description="记录考生意向专业，多个专业用逗号分隔")
def set_target_majors(target_majors: str) -> str:
    return f"已记录意向专业：{target_majors}"

@tool(description="记录考生弱势科目，多个科目用逗号分隔，无则留空")
def set_weak_subjects(weak_subjects: str) -> str:
    return f"已记录弱势科目：{weak_subjects}"

@tool(description="记录考生是否服从调剂，True为服从，False为不服从")
def set_accept_adjustment(accept_adjustment: bool) -> str:
    label = "服从" if accept_adjustment else "不服从"
    return f"已记录调剂意愿：{label}"



@tool(description="将报告内容保存为txt文件到report目录")
def generate_report(report_content: str) -> str:
    '''将agent生成的报告内容保存为txt文件'''
    report_dir = get_abs_path("report")
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"志愿填报报告_{timestamp}.txt"
    filepath = os.path.join(report_dir, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
    except Exception as e:
        return f"[错误] 报告保存失败: {str(e)}"

    return f"报告已保存到：{filepath}"




if __name__ == '__main__':
    # 模拟通过参数工具收集信息后保存报告
    print(set_rank.invoke(50000))
    print(set_province.invoke('辽宁'))
    print(set_priority.invoke('专业优先'))
    print(set_target_majors.invoke('自动化,人工智能'))
    print(set_weak_subjects.invoke(''))
    print(set_accept_adjustment.invoke(True))
    result = generate_report.invoke("这是一份测试报告内容")
    print(result)


