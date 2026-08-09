"""
PDF Report Generator using ReportLab.
Generates a multi-page professional AI Resume Analysis Report.
"""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# Brand colours
PRIMARY = colors.HexColor('#6366f1')
SECONDARY = colors.HexColor('#8b5cf6')
SUCCESS = colors.HexColor('#10b981')
WARNING = colors.HexColor('#f59e0b')
DANGER = colors.HexColor('#ef4444')
DARK = colors.HexColor('#1e1b4b')
MUTED = colors.HexColor('#64748b')
BG = colors.HexColor('#f8fafc')


def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=22, textColor=PRIMARY, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        'SectionHead', parent=styles['Heading2'],
        fontSize=14, textColor=DARK, spaceBefore=14, spaceAfter=6,
        borderWidth=0, borderColor=PRIMARY, borderPadding=4,
    ))
    styles.add(ParagraphStyle(
        'SubHead', parent=styles['Heading3'],
        fontSize=11, textColor=SECONDARY, spaceBefore=8, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        'BodyMuted', parent=styles['Normal'],
        fontSize=9, textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        'ScoreBig', parent=styles['Normal'],
        fontSize=28, alignment=TA_CENTER, textColor=PRIMARY, spaceAfter=4,
    ))
    return styles


def generate_pdf(analysis, market: dict) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = _get_styles()
    story = []

    # ── Header ──
    story.append(Paragraph('AI Resume Analysis Report', styles['ReportTitle']))
    story.append(HRFlowable(width='100%', color=PRIMARY, thickness=2))
    story.append(Spacer(1, 4*mm))

    name = analysis.candidate_name or 'Candidate'
    story.append(Paragraph(f'<b>{name}</b>', styles['Heading3']))
    meta_parts = []
    if analysis.email:
        meta_parts.append(analysis.email)
    if analysis.phone:
        meta_parts.append(analysis.phone)
    if meta_parts:
        story.append(Paragraph(' | '.join(meta_parts), styles['BodyMuted']))
    story.append(Spacer(1, 6*mm))

    # ── 1. Resume Overview ──
    story.append(Paragraph('1. Resume Overview', styles['SectionHead']))
    overview_data = [
        ['Category', analysis.get_resume_category_display()],
        ['Experience', f'{analysis.experience_years} years'],
        ['Education', analysis.education_level or 'Not detected'],
        ['Skills Found', str(len(analysis.extracted_skills))],
        ['Resume File', analysis.original_filename],
    ]
    story.append(_make_table(overview_data))
    story.append(Spacer(1, 4*mm))

    # ── 2. Skill Breakdown ──
    story.append(Paragraph('2. Skill Breakdown', styles['SectionHead']))
    if analysis.extracted_skills:
        skills_text = ', '.join(analysis.extracted_skills)
        story.append(Paragraph(skills_text, styles['Normal']))
    else:
        story.append(Paragraph('No skills detected.', styles['BodyMuted']))
    story.append(Spacer(1, 4*mm))

    # ── 3. Experience Analysis ──
    story.append(Paragraph('3. Experience Analysis', styles['SectionHead']))
    exp_data = [
        ['Total Experience', f'{analysis.experience_years} years'],
        ['Experience Score', f'{analysis.experience_score}/100'],
    ]
    story.append(_make_table(exp_data))
    story.append(Spacer(1, 4*mm))

    # ── 4. Resume Optimization Score ──
    story.append(Paragraph('4. Resume Optimization Score', styles['SectionHead']))
    score_label = analysis.score_label
    story.append(Paragraph(f'{analysis.overall_score}/100', styles['ScoreBig']))
    story.append(Paragraph(f'Rating: <b>{score_label}</b>', styles['Normal']))
    story.append(Spacer(1, 2*mm))

    score_breakdown = [
        ['Component', 'Weight', 'Score'],
        ['Skill Strength', '40%', f'{analysis.skill_score}'],
        ['Experience Relevance', '20%', f'{analysis.experience_score}'],
        ['Keyword Optimization', '15%', f'{analysis.keyword_score}'],
        ['Education', '10%', f'{analysis.education_score}'],
        ['Completeness', '15%', f'{analysis.completeness_score}'],
    ]
    story.append(_make_table(score_breakdown, header=True))
    story.append(Spacer(1, 4*mm))

    # ── 5. Job Fit Analysis ──
    story.append(Paragraph('5. Job Fit Analysis', styles['SectionHead']))
    if analysis.selected_job_role:
        story.append(Paragraph(
            f'Selected Role: <b>{analysis.selected_job_role.title}</b>', styles['Normal']))
        story.append(Paragraph(
            f'Match Percentage: <b>{analysis.job_match_percentage}%</b>', styles['Normal']))
        story.append(Spacer(1, 2*mm))
        if analysis.matched_skills:
            story.append(Paragraph('Matched Skills:', styles['SubHead']))
            story.append(Paragraph(', '.join(analysis.matched_skills), styles['Normal']))
    else:
        story.append(Paragraph('No job role was selected for matching.', styles['BodyMuted']))
    story.append(Spacer(1, 4*mm))

    # ── 6. Missing Skills ──
    story.append(Paragraph('6. Missing Skills', styles['SectionHead']))
    if analysis.missing_skills:
        for s in analysis.missing_skills:
            story.append(Paragraph(f'• {s}', styles['Normal']))
    else:
        story.append(Paragraph('No critical skill gaps identified.', styles['BodyMuted']))
    story.append(Spacer(1, 4*mm))

    # ── 7. Improvement Recommendations ──
    story.append(Paragraph('7. Improvement Recommendations', styles['SectionHead']))
    if analysis.suggestions:
        for i, s in enumerate(analysis.suggestions, 1):
            story.append(Paragraph(f'{i}. {s}', styles['Normal']))
            story.append(Spacer(1, 1*mm))
    story.append(Spacer(1, 4*mm))

    # ── 8. Suggested Career Paths ──
    story.append(Paragraph('8. Suggested Career Paths', styles['SectionHead']))
    if analysis.career_paths:
        cp_data = [['Role', 'Fit %', 'Category']]
        for cp in analysis.career_paths:
            cp_data.append([cp['role'], f"{cp['fit']}%", cp.get('category', '')])
        story.append(_make_table(cp_data, header=True))
    else:
        story.append(Paragraph('Not enough data to suggest career paths.', styles['BodyMuted']))

    # ── Footer ──
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width='100%', color=MUTED, thickness=0.5))
    story.append(Paragraph(
        'Generated by AI Resume Analyzer — Antigravity Recruitment Platform',
        ParagraphStyle('Footer', fontSize=8, textColor=MUTED, alignment=TA_CENTER),
    ))

    doc.build(story)
    buf.seek(0)
    return buf


def _make_table(data, header=False):
    """Create a styled table."""
    col_count = len(data[0]) if data else 0
    available = 170 * mm
    col_widths = [available / col_count] * col_count

    t = Table(data, colWidths=col_widths)
    style_cmds = [
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [BG, colors.white]),
    ]
    if header:
        style_cmds += [
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]
    t.setStyle(TableStyle(style_cmds))
    return t
