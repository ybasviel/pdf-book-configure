import PyPDF2
from pathlib import Path
import argparse
import yaml
import sys
from types import SimpleNamespace

def set_pdf_metadata_and_toc(input_pdf_path, output_pdf_path, author_info, toc_info, toc_page_diff):
    """
    PDFに著者名と目次を設定する関数
    
    Args:
        input_pdf_path (str): 入力PDFファイルのパス
        output_pdf_path (str): 出力PDFファイルのパス
        author_info (dict): 著者情報の辞書（例: {"/Author": "山田太郎", "/Title": "サンプルPDF"}）
        toc_info (list[Section]): Sectionオブジェクトのリスト
        toc_page_diff (int): 目次のページ番号とpdfのページ番号の差
    
    Returns:
        bool: 処理が成功したかどうか
    """

    toc_page_diff -= 1

    try:
        # PDFファイルを開く
        with open(input_pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()
            
            # すべてのページをコピー
            for page in reader.pages:
                writer.add_page(page)
            
            # メタデータを設定
            writer.add_metadata(author_info)
            
            # 目次を設定（Section, SubSection, SubSubSectionの階層構造に対応）
            def add_section_bookmarks(sections, parent=None):
                for section in sections:
                    # セクションを追加
                    section_bookmark = writer.add_outline_item(section.title, section.page + toc_page_diff, parent=parent)
                    
                    # サブセクションがあれば追加
                    if section.sub_sections:
                        for subsection in section.sub_sections:
                            subsection_bookmark = writer.add_outline_item(subsection.title, subsection.page + toc_page_diff, parent=section_bookmark)
                            
                            # サブサブセクションがあれば追加
                            if subsection.sub_sub_sections:
                                for subsubsection in subsection.sub_sub_sections:
                                    writer.add_outline_item(subsubsection.title, subsubsection.page + toc_page_diff, parent=subsection_bookmark)
            
            add_section_bookmarks(toc_info)
            
            # 新しいPDFファイルを保存
            with open(output_pdf_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

def dict_to_section(section_dict):
    """辞書からSectionオブジェクトを再構築する関数"""
    section = SimpleNamespace()
    section.title = section_dict["title"]
    section.page = section_dict["page"]
    
    if "sub_sections" in section_dict and section_dict["sub_sections"]:
        section.sub_sections = [dict_to_section(sub) for sub in section_dict["sub_sections"]]
    else:
        section.sub_sections = []
        
    if "sub_sub_sections" in section_dict and section_dict["sub_sub_sections"]:
        section.sub_sub_sections = []
        for sub in section_dict["sub_sub_sections"]:
            sub_sub = SimpleNamespace()
            sub_sub.title = sub["title"]
            sub_sub.page = sub["page"]
            section.sub_sub_sections.append(sub_sub)
    else:
        section.sub_sub_sections = []
        
    return section

if __name__ == "__main__":
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='YAMLファイルからPDFに著者名と目次を設定するプログラム')
    parser.add_argument('--input', '-i', type=str, default="info.yaml", help='入力YAMLファイルのパス(デフォルトはinfo.yaml)')
    parser.add_argument('--output-dir', '-o', type=str, default="output", help='出力ディレクトリのパス')
    parser.add_argument('--pdf', '-p', type=str, help='PDFファイルのパス（YAMLファイルで指定されていない場合に使用）')
    
    args = parser.parse_args()

    # YAMLファイルを読み込む
    yaml_path = Path(args.input)
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"YAMLファイルの読み込み中にエラーが発生しました: {e}")
        sys.exit(1)

    # データを取得
    input_pdf_path = args.pdf if args.pdf else data.get("input_pdf")
    if not input_pdf_path:
        print("PDFファイルが指定されていません。YAMLファイルで指定するか、--pdfオプションを使用してください。")
        sys.exit(1)
    
    input_pdf = Path(input_pdf_path)
    if not input_pdf.exists():
        print(f"指定されたPDFファイルが存在しません: {input_pdf}")
        sys.exit(1)
    
    author_info = data.get("author_info", {})
    toc_dict_list = data.get("toc_info", [])
    toc_page_diff = data.get("toc_page_diff", 0)

    # 目次情報をオブジェクトに変換
    toc_info = [dict_to_section(section_dict) for section_dict in toc_dict_list]

    # 出力先の設定
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    output_pdf = output_dir / input_pdf.name

    # 情報を表示
    print(f"入力PDFファイル: {input_pdf}")
    print(f"出力PDFファイル: {output_pdf}")
    print(f"著者名: {author_info.get('/Author', '')}")
    print(f"タイトル: {author_info.get('/Title', '')}")
    print(f"目次項目数: {len(toc_info)}")
    print(f"目次ページ差分: {toc_page_diff}")

    # 確認
    proceed = input("\nPDFに書き込みを行いますか？ (Y/n): ").strip().lower()
    if proceed != 'y' and proceed != '':
        print("処理を中止します。")
        sys.exit(0)

    # PDFに適用
    result = set_pdf_metadata_and_toc(input_pdf, output_pdf, author_info, toc_info, toc_page_diff)
    print(f"処理結果: {result}") 