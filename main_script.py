import sys
import os
import threading
import tkinter as tk
import time
from tkinter import filedialog
from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QLabel, 
    QDialog,
    QPushButton, 
    QVBoxLayout,
    QHBoxLayout, 
    QScrollArea,
    QComboBox, 
    QProgressBar, 
    QSplitter,
    QFileDialog, 
    QInputDialog,
    QSizePolicy,
    QTextEdit,
    QMessageBox,
    QLineEdit
)
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt,Q_ARG,QMetaObject,QEvent
from PyQt5.QtGui import QFont,QTextOption 
from tqdm import tqdm
from pdfminer.high_level import extract_text
import SparkApi
import re


# API credentials
APP_ID = "0340274e"
API_SECRET = "MjgwOTA0MTNjNWQ4NzI1MjE5ZDY2MWI3"
API_KEY = "06675b881f331826f92dd7ed667f07f5"
SPARK_URL = "wss://spark-api.xf-yun.com/v4.0/chat"
DOMAIN = "4.0Ultra"

# Extract text from a PDF file using PDFMiner
def parse_pdf(file_path):
    try:
        text = extract_text(file_path)
        return text
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return ""

# Preprocess content to remove potential sensitive keywords
def preprocess_content(content):
    sensitive_words = ["national security", "politics", "violence", "religion", "terrorism", "illegal", "inappropriate"]
    for word in sensitive_words:
        content = content.replace(word, "[REDACTED]")
    content = re.sub(r'\(cid:\d+\)', ' ', content)  # Remove (cid) placeholders
    return content

# Function to split text into smaller chunks based on a max length
def split_text_into_chunks(text, max_length=1500):
    chunks = []
    while len(text) > max_length:
        split_index = text.rfind(" ", 0, max_length)  # Find last space before max length
        chunks.append(text[:split_index])
        text = text[split_index:].strip()
    chunks.append(text)  # Append the remaining text
    return chunks

# Save results as Markdown
def save_as_markdown(filename, content):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists
    md_filename = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.md")
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write("# Summary and Analysis Report\n\n")
        f.write(content)
    print(f"\nMarkdown report saved to: {md_filename}")

# Language mapping function
def map_language_input(language_input):
    language_mapping = {
        "english": "en",
        "en": "en",
        "chinese": "zh",
        "zh": "zh",
        "korean": "ko",  # Add Korean support
        "ko": "ko",  # Also handle the code as 'ko'
        "spanish": "es",
        "fr": "fr",  # French support
    }
    return language_mapping.get(language_input.lower())


def process_file(file_path, save_func, task_name="Processing", language="en", progress_bar=None):
    print(f"\n{task_name} file: {file_path}")
    pdf_content = parse_pdf(file_path)
    if pdf_content:
        pdf_content = preprocess_content(pdf_content)
        # Split the content into chunks
        text_chunks = split_text_into_chunks(pdf_content)
        
        SparkApi.answer = ""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Process each chunk
                for chunk in text_chunks:
                    questions = initialize_questions_wrapper(chunk, language=language)
                    SparkApi.main(APP_ID, API_KEY, API_SECRET, SPARK_URL, DOMAIN, questions)
                    save_func(os.path.basename(file_path), SparkApi.answer)
                if progress_bar:
                    progress_bar.setValue(100)
                break
            except Exception as e:
                print(f"Request failed: {e}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(5)  # Wait 5 seconds before retrying
                else:
                    print("Max retries reached. Skipping this file.")

# Wrapper to initialize questions based on language
def initialize_questions_wrapper(pdf_content, language="en"):
    """
    Wrapper to initialize questions based on the selected language.

    Args:
    - pdf_content: The content extracted from the PDF.
    - language: The language for the output, "en" for English or "zh" for Chinese.

    Returns:
    - A list of questions tailored to the specified language.
    """
    if language.lower() == "en":
        return [
            {"role": "system", "content": "You are a highly skilled research scholar specializing in writing and analyzing various types of academic papers, including technology, literature, and social sciences. I will send you some academic documents; please carefully read the content and provide a detailed explanation of each part, answering my questions thoroughly. This is very important, so I expect you to respond diligently, ensuring that every question is answered accurately and in-depth. Please write your answers in a professional academic tone."},
            {"role": "user", "content": f"Based on the following content, analyze this paper:\n\n{pdf_content}\n\nPlease address the following points:\n1. Provide an overview of the main content of this paper, summarizing its core ideas and conclusions succinctly.\n2. Explain the core problem being studied in this paper and why the author chose to investigate this issue, as well as its importance in the field.\n3. Describe the definitions of the key variables in this paper, including their characteristics and scope, and explain their specific applications and significance in the study.\n4. Discuss the experimental design of this paper, including its objectives, methods, steps, control and measurement of variables, sample selection, and data analysis methods.\n5. Summarize the experimental results, including key findings and main conclusions from data analysis. Explain how these results support or refute the hypotheses and briefly discuss their significance.\n6. Summarize the main conclusions of this paper, how they address the research questions or hypotheses, and their significance and impact in the research field.\n7. Identify the theoretical framework this paper is based on, briefly introducing the key concepts and how they are applied in the study to support the research.\n8. Summarize the literature review in this paper, including key topics, the current state of the research field, gaps in existing studies, and how this content lays the groundwork for the research.\n9. Discuss the limitations of this study and the authors' suggestions for future research, including the main constraints, their impact on results, and potential directions for improvement."}
        ]
    elif language.lower() == "zh":
        return [
        {"role": "system", "content": """您是一位资深的学术研究专家，专门从事各类学术论文的分析和研究。请您以专业、严谨且详尽的方式分析论文，确保：
                1. 分析内容全面且深入，每个部分都要有充分的论述和举例
                2. 保持专业的学术语言风格，同时确保表述清晰易懂
                3. 特别注意引用论文中的具体数据、方法和结论来支持您的分析
                4. 对重要观点和创新点进行深入剖析
                5. 关注研究方法的具体实施细节和理论支撑
                请确保您的分析既有学术深度，又能让读者清楚理解研究的价值和贡献。"""},
        
        {"role": "user", "content": f"""请对以下论文进行深入分析：\n\n{pdf_content}\n\n
        请按照以下框架进行详细分析，每个部分都需要具体和深入的讨论：

        1. 文章综述（200字以上）：
        - 研究主题和核心问题
        - 研究背景和现实意义
        - 主要研究框架和方法
        - 核心发现和主要贡献

        2. 研究问题剖析（200字以上）：
        - 问题的提出背景
        - 问题的理论意义
        - 问题的现实意义
        - 研究创新点

        3. 核心概念和变量（150字以上）：
        - 主要概念的定义和解释
        - 变量的选择依据
        - 变量间的关系
        - 操作化定义

        4. 研究设计与方法（200字以上）：
        - 研究框架详述
        - 数据来源和处理
        - 研究方法选择依据
        - 具体实施步骤
        - 研究工具和模型

        5. 研究发现与讨论（200字以上）：
        - 主要研究发现
        - 数据分析结果
        - 假设验证情况
        - 结果的理论意义
        - 结果的实践价值

        6. 理论贡献与应用：
        - 对现有理论的补充和发展
        - 研究结论的应用价值
        - 对实践的指导意义

        7. 研究局限与展望：
        - 研究的不足之处
        - 潜在的改进空间
        - 未来研究方向建议

        请确保分析既有深度又有广度，并注意论述的逻辑性和连贯性。"""}
    ]
    else:
        raise ValueError("Unsupported language. Please choose English ('en') or Chinese ('zh').")

def initialize_summary_questions_wrapper(pdf_content, language):
    """综合分析的prompt"""
    if language.lower() == "en":
        return [
            {"role": "system", "content": """You are a senior research analyst specializing in comprehensive analysis of multiple academic papers. Your task is to:
1. Identify common themes and patterns across the papers
2. Compare and contrast different approaches and findings
3. Synthesize key insights and implications
4. Provide a holistic view of the research field
Please ensure your analysis is thorough, well-structured, and academically rigorous."""},
            {"role": "user", "content": f"""Please provide a comprehensive analysis of the following collection of academic papers:\n\n{pdf_content}\n\n
Please address the following aspects in your analysis and prepare your answer in no less than 1000 words:

1. Overview and Common Themes (30%)
   - Identify and discuss the main themes that emerge across these papers
   - Analyze how these papers relate to and complement each other
   - Discuss the broader research context they collectively address

2. Methodological Analysis (20%)
   - Compare and contrast the research methods used
   - Evaluate the strengths and limitations of different approaches
   - Identify methodological trends and innovations

3. Findings Synthesis (25%)
   - Synthesize the key findings across all papers
   - Identify areas of consensus and disagreement
   - Discuss the collective implications of these findings

4. Research Gaps and Future Directions (15%)
   - Identify gaps that emerge when considering these papers together
   - Suggest potential directions for future research
   - Discuss emerging trends and opportunities

5. Practical Implications (10%)
   - Discuss the collective practical implications
   - Provide recommendations for practitioners
   - Identify potential applications of the research

Please ensure your analysis focuses on the relationships and patterns across the papers, rather than analyzing each paper individually."""}
        ]
    elif language.lower() == "zh":
        return [
            {"role": "system", "content": """您是一位专门从事多篇学术论文综合分析的资深研究专家。您的任务是：
            1. 识别论文间的共同主题和模式
            2. 对比不同研究的方法和发现
            3. 综合关键见解和启示
            4. 提供研究领域的整体观点
            请确保您的分析全面、结构清晰，并保持学术严谨性。"""},
            
            {"role": "user", "content": f"""请对以下学术论文集合进行综合分析：\n\n{pdf_content}\n\n
        请在分析中涵盖以下方面,并确保生成的回答字数超过1000字：

        1. 整体概述与共同主题（30%）：
        - 识别并讨论这些论文中出现的主要主题
        - 分析论文之间的关联性和互补性
        - 讨论它们共同涉及的更广泛研究背景

        2. 研究方法分析（20%）：
        - 比较和对比使用的研究方法
        - 评估不同方法的优势和局限性
        - 识别方法论趋势和创新点

        3. 研究发现综合（25%）：
        - 综合所有论文的关键发现
        - 找出研究共识和分歧之处
        - 讨论这些发现的综合启示

        4. 研究空白与未来方向（15%）：
        - 识别这些论文共同反映的研究空白
        - 建议未来可能的研究方向
        - 讨论新兴趋势和机会

        5. 实践启示（10%）：
        - 讨论综合研究的实践意义
        - 为实践者提供建议
        - 识别研究的潜在应用领域

        请确保分析着重于论文之间的关系和模式，而不是单独分析每篇论文。"""}
        ]
        

class UpdateSignals(QObject):
    update_output = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    update_status = pyqtSignal(str)
    show_message = pyqtSignal(str)
    request_input = pyqtSignal()  # 添加请求输入信号
    input_received = pyqtSignal(str)  # 添加接收输入信号
    
# GUI for the main program
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 初始化信号对象
        self.signals = UpdateSignals()

        # 连接信号到对应的槽
        self.signals.update_output.connect(self._update_output)
        self.signals.update_progress.connect(self._update_progress)
        self.signals.update_status.connect(self._update_status)
        self.signals.show_message.connect(self.show_completion_message)
        self.signals.request_input.connect(self._show_input_dialog)  
        
        # 用于存储用户输入的变量
        self.input_lock = threading.Lock()
        self.user_input = None
        self.input_event = threading.Event()
        
        # Window setup
        self.setWindowTitle("PDF Analyzer")
        self.setMinimumSize(1600, 920)

        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left panel (controls)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        left_layout.setContentsMargins(20, 30, 20, 20)
        left_layout.setSpacing(25)

        # Title
        title_label = QLabel("PDF Analysis Tool")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        title_label.setStyleSheet("margin-bottom: 20px;")
        left_layout.addWidget(title_label)

        # Language selection
        language_container = QWidget()
        language_layout = QHBoxLayout(language_container)
        language_layout.setContentsMargins(0, 0, 0, 20)

        language_label = QLabel("Select Language:")
        language_label.setFont(QFont("Arial", 14))
        language_label.setStyleSheet("color: #333333;")

        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Chinese"])
        self.language_combo.setFixedWidth(170)
        self.language_combo.setFont(QFont("Arial", 12))
        self.language_combo.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 30px;
                background-color: white;
            }
        """)

        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(language_container)

        button_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                padding: 5px 20px;
                font-size: 25px;
                font-weight: bold;
                text-align: center;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
        """

        # Buttons container 增加顶部间距
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setAlignment(Qt.AlignHCenter)
        buttons_layout.setSpacing(25)  
        buttons_layout.setContentsMargins(10, 50, 10, 50)  

        button_names = [
            "Select a PDF File",
            "Process All PDFs in Folder",
            "Summarize and Analyze PDFs"
        ]

        self.buttons = []
        for name in button_names:
            button = QPushButton(name)
            font_metrics = button.fontMetrics()
            text_width = font_metrics.boundingRect(name).width()
            button_width = text_width + 120 
                
            button.setFixedHeight(90)
            button.setStyleSheet(button_style)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            buttons_layout.addWidget(button)
            self.buttons.append(button)

        [self.select_file_button, self.process_folder_button, 
        self.summarize_folder_button] = self.buttons


        # 在按钮容器和进度条之间添加更大的间距
        left_layout.addWidget(buttons_container)
        left_layout.addSpacing(50)  # 增加与进度条的间距

        # Progress section
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(20, 20, 20, 20)  
        progress_layout.setSpacing(15) 

        self.progress_label = QLabel("Progress:")
        self.progress_label.setFont(QFont("Arial", 14))
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(60)  
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                font-size: 18px;
                font-weight: bold;
                background-color: white;
                margin-top: 10px; 
                margin-bottom: 10px;  
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        # Status label with increased spacing
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setStyleSheet("""
            color: #0047AB;
            margin-top: 20px;
            padding: 10px 0;
        """)
        progress_layout.addWidget(self.status_label)

        # 添加进度容器并在下方添加弹性空间
        left_layout.addWidget(progress_container)
        left_layout.addStretch(1)

        # Right panel (output display)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)

        output_label = QLabel("Analysis Results")
        output_label.setFont(QFont("Arial", 18, QFont.Bold))
        output_label.setAlignment(Qt.AlignCenter)
        output_label.setStyleSheet("margin-bottom: 10px;")
        right_layout.addWidget(output_label)

        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                font-family: "Courier New";
                font-size: 20px;
                line-height: 1.5;
            }
        """)
        right_layout.addWidget(self.output_text)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(right_panel, 3)

        self.setLayout(main_layout)

        self.select_file_button.clicked.connect(self.select_pdf_file)
        self.process_folder_button.clicked.connect(self.process_folder)
        self.summarize_folder_button.clicked.connect(self.summarize_folder)
        
    @pyqtSlot()
    def _show_input_dialog(self):
        """在主线程中显示输入对话框"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("问题输入")
            dialog.setMinimumSize(600, 400)  # 设置最小尺寸
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)  # 添加最大化/最小化按钮
            
            # 创建主布局
            main_layout = QVBoxLayout(dialog)
            main_layout.setContentsMargins(20, 20, 20, 20)  # 设置边距
            main_layout.setSpacing(15)  # 设置组件间距
            
            # 创建文本输入框
            text_edit = QTextEdit(dialog)
            text_edit.setPlaceholderText("请输入您的问题 (输入 'q' 退出)：")
            text_edit.setAcceptRichText(False)  # 禁用富文本格式
            text_edit.setWordWrapMode(QTextOption.WrapAnywhere)  # 自动换行
            text_edit.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: white;
                    font-size: 20px;
                }
            """)
            main_layout.addWidget(text_edit)
            
            # 按钮容器 - 使用水平布局将按钮置于底部居中
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(0, 10, 0, 0)  # 上方添加间距
            
            # 创建提交按钮
            submit_button = QPushButton("提交问题", dialog)
            submit_button.setFixedSize(200, 50)  # 设置固定大小
            submit_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #388E3C;
                }
            """)
            
            # 设置按钮布局
            button_layout.addStretch(1)  # 左侧弹性空间
            button_layout.addWidget(submit_button)
            button_layout.addStretch(1)  # 右侧弹性空间
            
            # 将按钮容器添加到主布局
            main_layout.addWidget(button_container)
            
            # 提交按钮事件
            def on_submit():
                text = text_edit.toPlainText().strip()
                with self.input_lock:
                    self.user_input = text if text else 'q'
                    self.input_event.set()
                dialog.accept()
            
            submit_button.clicked.connect(on_submit)
            
            # 设置回车键提交
            text_edit.installEventFilter(self)
            
            dialog.exec_()
            
        except Exception as e:
            print(f"Dialog error: {e}")
            with self.input_lock:
                self.user_input = 'q'
                self.input_event.set()

    # 增加事件过滤器处理回车键提交功能
    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and
                event.key() == Qt.Key_Return and
                event.modifiers() == Qt.ControlModifier):
            # Ctrl+Enter提交
            text = source.toPlainText().strip()
            with self.input_lock:
                self.user_input = text if text else 'q'
                self.input_event.set()
            source.parent().accept()
            return True
        return super().eventFilter(source, event)
    def show_individual_progress(self, current, total):
        """显示单个文件进度"""
        self.status_label.setText(f"Processing ({current}/{total})")
        self.progress_bar.setFormat(f"当前文件: {current}/{total} - %p%")

    def get_user_input(self):
        """线程安全地获取用户输入"""
        try:
            self.input_event.clear()
            self.signals.request_input.emit()
            self.input_event.wait()
            with self.input_lock:
                result = self.user_input
                self.user_input = None
                return result
        except Exception as e:
            print(f"Input error: {e}")
            return 'q'
        
    @pyqtSlot(str)
    def _update_output(self, text):
        """在主线程中更新输出文本"""
        self.output_text.append(text)
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )

    def update_output(self, text):
        """从线程中安全地更新输出"""
        self.signals.update_output.emit(text)

    @pyqtSlot(int)
    def _update_progress(self, value):
        """在主线程中更新进度条"""
        self.progress_bar.setValue(value)

    def update_progress(self, value):
        """从线程中安全地更新进度"""
        self.signals.update_progress.emit(int(value))

    @pyqtSlot(str)
    def _update_status(self, status):
        """在主线程中更新状态标签"""
        self.status_label.setText(status)

    def update_status(self, status):
        """从线程中安全地更新状态"""
        self.signals.update_status.emit(status)

    def resizeEvent(self, event):
        """处理窗口大小改变事件"""
        super().resizeEvent(event)
        width = self.width()
        button_width = min(max(300, width // 4), 400)
        for button in self.buttons:
            button.setFixedWidth(button_width)

    def select_pdf_file(self):
        """选择单个PDF文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.process_file(file_path)

    def process_folder(self):
        """选择文件夹处理多个PDF"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select a Folder")
        if folder_path:
            self.process_pdfs_in_folder(folder_path)

    def summarize_folder(self):
        """选择文件夹总结分析PDF"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select a Folder")
        if folder_path:
            self.summarize_multiple_pdfs(folder_path)

    def process_file(self, file_path):
        """处理单个文件"""
        language = map_language_input(self.language_combo.currentText().lower())
        threading.Thread(target=self._process_file_thread, args=(file_path, language)).start()

    def process_pdfs_in_folder(self, folder_path):
        """处理文件夹中的所有PDF"""
        language = map_language_input(self.language_combo.currentText().lower())
        threading.Thread(target=self._process_folder_thread, args=(folder_path, language)).start()

    def summarize_multiple_pdfs(self, folder_path):
        """总结分析文件夹中的PDF"""
        language = map_language_input(self.language_combo.currentText().lower())
        threading.Thread(target=self._summarize_folder_thread, args=(folder_path, language)).start()

    def _process_file_thread(self, file_path, language):
        """处理单个文件的线程"""
        try:
            total_steps = 4
            current_step = 0
            # 步骤1: 开始处理
            self.update_status(f"Processing: {os.path.basename(file_path)}")
            self.update_output(f"\n开始分析文件: {os.path.basename(file_path)}\n")
            self.update_progress(int((current_step / total_steps) * 100))
            current_step += 1
            
            # 步骤2: 读取PDF
            self.update_status("Reading PDF content...")
            pdf_content = parse_pdf(file_path)
            if pdf_content:
                self.update_progress(int((current_step / total_steps) * 100))
                current_step += 1
                
                # 步骤3: 预处理内容
                self.update_status("Preprocessing content...")
                pdf_content = preprocess_content(pdf_content)
                questions = initialize_questions_wrapper(pdf_content, language)
                SparkApi.answer = ""
                self.update_progress(int((current_step / total_steps) * 100))
                current_step += 1
                
                # 步骤4: 分析内容
                self.update_status("Analyzing content...")
                initial_analysis = ""  # 存储初始分析结果
                
                def update_callback(text):
                    self.update_output(text)
                    nonlocal initial_analysis
                    initial_analysis += text  
                    if SparkApi.answer:
                        base_progress = 75
                        content_length = len(SparkApi.answer)
                        estimated_progress = min(
                            base_progress + (content_length / 3000) * 20,
                            95
                        )
                        self.update_progress(int(estimated_progress))
                        self.update_status("Processing analysis results...")
                
                SparkApi.set_callback(update_callback)
                SparkApi.main(APP_ID, API_KEY, API_SECRET, SPARK_URL, DOMAIN, questions)
                
                # 保存初始分析结果
                self.update_status("Saving initial analysis...")
                save_as_markdown(os.path.basename(file_path), SparkApi.answer)
                self.update_progress(100)
                
                # 交互式问答
                self.update_output("\n\n=== 问答模式 ===")
                self.update_output("\n您可以针对文档内容提问，每次提问后等待回答。")
                self.update_output("\n输入 'q' 退出问答模式\n")

                qa_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_qa.md"
                qa_filepath = os.path.join("output", qa_filename)

                while True:
                    # 使用线程安全的方式获取用户输入
                    text = self.get_user_input()
                    
                    if not text or text.lower() == 'q':
                        self.update_output("\n=== 问答模式结束 ===\n")
                        break

                    if not text.strip():
                        continue

                    # 构建问答上下文
                    qa_questions = [
   
                    {"role": "system", "content": "You are an AI assistant with expertise in academic analysis and research. Your task is to provide detailed, evidence-based answers to academic questions based on the content of the provided paper. Do not respond to non-academic queries or expressions of gratitude. Only answer direct, relevant questions related to the paper."},

                    {"role": "user", "content": f"Based on the analysis of the academic paper provided, please answer the following question. Be sure to support your answer with relevant content from the paper.\n\n{pdf_content}\n\nQuestion: {text}"}
            ]
                    
                    # 在程序中，增加检查机制来避免无关输入
                    def is_valid_question(question):
                        # 如果问题只是感谢或无意义的输入，可以跳过
                        irrelevant_phrases = ["感谢", "谢谢", "谢谢你", "感谢你的回答"]
                        for phrase in irrelevant_phrases:
                            if phrase in question:
                                return False
                        return True
                    
                    # 执行问答
                    self.update_output(f"\nQ: {text}\n")
                    self.update_status("正在处理您的问题...")
                    SparkApi.answer = ""
                    
                    def qa_callback(answer_text):
                        self.update_output(answer_text)
                    
                    SparkApi.set_callback(qa_callback)
                    SparkApi.main(APP_ID, API_KEY, API_SECRET, SPARK_URL, DOMAIN, qa_questions)
                    
                    with open(qa_filepath, "a", encoding="utf-8") as f:
                        f.write(f"\nQ: {text}\nA: {SparkApi.answer}\n")
                    
                    self.update_status("Ready for next question")
                
                # 完成处理
                self.update_status("Analysis completed")
                self.signals.show_message.emit(os.path.basename(file_path))
                SparkApi.answer = ""
                
            else:
                self.update_output(f"\nError: Could not read PDF file: {file_path}\n")
                self.update_status("Error processing file")
                self.update_progress(0)
                
        except Exception as e:
            self.update_output(f"\nError processing file: {str(e)}\n")
            self.update_status("Error occurred")
            self.update_progress(0)
        finally:
            QApplication.processEvents() 

    def _process_single_file(self, file_path, language, progress_callback=None):
        """处理单个文件的辅助方法"""
        try:
            self.update_status(f"Processing: {os.path.basename(file_path)}")
            if progress_callback:
                progress_callback(int(25))
            self.update_output("\n正在读取PDF内容...\n")
            pdf_content = parse_pdf(file_path)
            
            if pdf_content:
                # 预处理
                if progress_callback:
                    progress_callback(int(50))
                self.update_output("正在预处理内容...\n")
                pdf_content = preprocess_content(pdf_content)
                questions = initialize_questions_wrapper(pdf_content, language)
                SparkApi.answer = ""
                
                # 分析
                if progress_callback:
                    progress_callback(int(75))
                self.update_output("开始分析内容...\n")
                
                def update_callback(text):
                    self.update_output(text)
                    if progress_callback:
                        current_progress = min(75 + (len(SparkApi.answer) / 1000), 95)
                        progress_callback(int(current_progress))
                
                SparkApi.set_callback(update_callback)
                SparkApi.main(APP_ID, API_KEY, API_SECRET, SPARK_URL, DOMAIN, questions)
                
                # 保存结果
                initial_analysis = SparkApi.answer
                save_as_markdown(os.path.basename(file_path), initial_analysis)
                
                if progress_callback:
                    progress_callback(int(100))
                self.update_status("Initial analysis completed")
                
                self.update_output("\n提示: 如需详细问答，请使用单个文件处理功能\n")
                self.signals.show_message.emit(os.path.basename(file_path))
                
            else:
                self.update_output(f"\nError: Could not read PDF file: {file_path}\n")
                self.update_status("Error processing file")
                if progress_callback:
                    progress_callback(int(0))
        except Exception as e:
            self.update_output(f"\nError processing {os.path.basename(file_path)}: {str(e)}\n")
            if progress_callback:
                progress_callback(int(0))
                
    def _process_folder_thread(self, folder_path, language):
        """处理文件夹的线程（修复版）"""
        try:
            pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
            total_files = len(pdf_files)
            
            if total_files == 0:
                self.update_output("\n未找到PDF文件\n")
                self.update_status("没有可处理文件")
                return
                
            self.update_output(f"\n发现 {total_files} 个PDF文件待处理\n")
            
            for i, pdf_file in enumerate(pdf_files, 1):
                file_path = os.path.join(folder_path, pdf_file)
                self.update_status(f"正在处理 ({i}/{total_files}): {pdf_file}")
                
                # 为每个文件创建独立线程
                thread = threading.Thread(
                    target=self._process_single_in_folder,
                    args=(file_path, language, i, total_files)
                )
                thread.start()
                thread.join()  # 等待当前文件处理完成
                
                # 更新总进度
                progress = int((i / total_files) * 100)
                self.update_progress(progress)
            
            self.update_status("全部文件处理完成")
            
        except Exception as e:
            self.update_output(f"\n处理文件夹出错: {str(e)}\n")
            self.update_status("发生错误")

    def _process_single_in_folder(self, file_path, language, index, total):
        """在文件夹处理中处理单个文件"""
        try:
            self.update_output(f"\n▶ 正在处理文件 ({index}/{total}): {os.path.basename(file_path)}\n")
            
            # 重置进度条为当前文件进度
            self.update_progress(0)
            
            # 执行文件处理
            pdf_content = parse_pdf(file_path)
            if not pdf_content:
                self.update_output("⚠ 无法读取文件内容\n")
                return
                
            pdf_content = preprocess_content(pdf_content)
            questions = initialize_questions_wrapper(pdf_content, language)
            SparkApi.answer = ""
            
            # 设置进度回调（0-80%）
            def progress_callback(value):
                adjusted_value = int(value * 0.8)  # 单个文件占80%进度
                self.update_progress(adjusted_value)
            
            # 处理分析结果
            def update_callback(text):
                self.update_output(text)
                if SparkApi.answer:
                    current_progress = min(80, 10 + int(len(SparkApi.answer)/2000 * 70))
                    progress_callback(current_progress)
            
            SparkApi.set_callback(update_callback)
            SparkApi.main(APP_ID, API_KEY, API_SECRET, SPARK_URL, DOMAIN, questions)
            
            # 保存结果（占最后20%进度）
            save_as_markdown(os.path.basename(file_path), SparkApi.answer)
            self.update_progress(100)
            self.update_output(f"\n✔ 完成处理: {os.path.basename(file_path)}\n")
            
        except Exception as e:
            self.update_output(f"\n处理文件出错: {str(e)}\n")

    def _summarize_folder_thread(self, folder_path, language):
        """总结文件夹的线程"""
        try:
            self.update_output("\nStarting folder summary...\n")
            combined_content = ""
            pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]

            # 第一阶段：读取和合并所有PDF内容 (0-50%)
            for i, pdf_file in enumerate(pdf_files, 1):
                file_path = os.path.join(folder_path, pdf_file)
                self.update_output(f"Reading file {i}/{len(pdf_files)}: {pdf_file}")
                pdf_content = parse_pdf(file_path)
                if pdf_content:
                    combined_content += f"\n\n--- {file_path} ---\n\n{preprocess_content(pdf_content)}"
                
                progress = int((i / len(pdf_files)) * 50)
                self.update_progress(progress)

            if combined_content.strip():
                # 第二阶段：综合分析 (50-100%)
                self.update_output("\nAnalyzing combined content...\n")
                
                # 使用合并的内容进行一次分析
                questions = initialize_summary_questions_wrapper(combined_content, language)
                SparkApi.answer = ""
                
                def update_callback(text):
                    self.update_output(text)
                    if SparkApi.answer:
                        progress = min(50 + (len(SparkApi.answer) / 3000) * 45, 95)
                        self.update_progress(int(progress))

                SparkApi.set_callback(update_callback)
                SparkApi.main(APP_ID, API_KEY, API_SECRET, SPARK_URL, DOMAIN, questions)

                # 合并所有答案
                all_answers = SparkApi.answer

                # 保存结果
                self.update_status("Saving combined analysis...")
                save_as_markdown("summary_analysis_result", all_answers)

                self.update_output("\n\n=== Comprehensive Analysis Q&A Mode ===")
                self.update_output("\nYou can ask questions about the combined content of all documents. Please wait for the response after each question.")
                self.update_output("\nType 'q' to exit the Q&A mode\n")

                qa_filename = "summary_analysis_qa.md"
                qa_filepath = os.path.join("output", qa_filename)

                # 进入问答模式，限制循环次数或超时，避免死循环
                self.handle_qa_mode(qa_filepath, combined_content)

                self.update_progress(100)
                self.update_status("Analysis completed")
                self.signals.show_message.emit("summary_analysis")
                
            else:
                self.update_output("\nNo valid content found in PDFs\n")
                self.update_status("No content to process")
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("No usable content found in the folder!")
                msg.setWindowTitle("Warning")
                msg.exec_()

        except Exception as e:
            self.update_output(f"\nError during summary: {str(e)}\n")
            self.update_status("Error occurred")

    def handle_qa_mode(self, qa_filepath, combined_content):
        """Handles the Q&A mode with a timeout mechanism to avoid infinite loop"""
        timeout = 300  # Timeout after 5 minutes
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                self.update_output("\nAutomatically exiting Q&A mode due to timeout\n")
                break

            text = self.get_user_input()

            if not text or text.lower() == 'q':
                self.update_output("\n=== Q&A Mode Ended ===\n")
                break

            if not text.strip():
                continue

            # Build the Q&A context based on all documents combined
            qa_questions = [
                {"role": "system", "content": "You are a helpful assistant analyzing multiple academic papers. Please provide answers based on the comprehensive analysis of all papers."},
                {"role": "user", "content": f"Based on the analysis of these papers:\n\n{combined_content}\n\nPlease answer this question:\n{text}"}
            ]

            self.update_output(f"\nQ: {text}\n")
            self.update_status("Processing question...")
            SparkApi.answer = ""

            def qa_callback(answer_text):
                self.update_output(answer_text)

            SparkApi.set_callback(qa_callback)
            SparkApi.main(APP_ID, API_KEY, API_SECRET, SPARK_URL, DOMAIN, qa_questions)

            with open(qa_filepath, "a", encoding="utf-8") as f:
                f.write(f"\nQ: {text}\nA: {SparkApi.answer}\n")

            self.update_status("Ready for next question")

            

    def show_completion_message(self, filename):
            """显示处理完成的消息框"""
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Analysis Complete")
            msg.setInformativeText(f"Analysis of {filename} has been completed.\nResults have been saved to the output folder.")
            msg.setWindowTitle("Success")
            
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                    font-size: 14px;
                }
                QPushButton {
                    padding: 5px 15px;
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 4px;
                    min-width: 80px;
                    min-height: 25px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            msg.show()

# Main function to run the GUI application
def main():
    try:
        QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_Use96Dpi)
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())

    except Exception as e:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(f"Unexpected error occurred: {str(e)}")
        msg.setWindowTitle("Error")
        msg.exec_()
        sys.exit(1)  

if __name__ == '__main__':
    main()

    