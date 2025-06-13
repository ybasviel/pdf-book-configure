from google import genai
import os
from pathlib import Path
from typing import Optional
import dataclasses
import argparse
import yaml
import pdf2image
import PyPDF2

"""
著者情報
"""
@dataclasses.dataclass
class AuthorInfo:
    author: str
    title: str


"""
目次の階層構造
"""
@dataclasses.dataclass
class SubSubSection:
    title: str
    page: int

@dataclasses.dataclass
class SubSection:
    title: str
    page: int
    sub_sub_sections: Optional[list[SubSubSection]]

@dataclasses.dataclass
class Section:
    title: str
    page: int
    sub_sections: Optional[list[SubSection]]



client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def gemini_api_call(save_paths: list[Path], prompt: str, response_schema: type[dataclasses.dataclass]):
    """
    Gemini APIを呼び出して画像を分析する関数
    """
    my_files = []
    for save_path in save_paths:
        my_file = client.files.upload(file=save_path)
        my_files.append(my_file)

    contents = []
    for my_file in my_files:
        contents.append(my_file)

    contents.append(prompt)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=my_files,
        config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
        },
    )

    return response.parsed


def extract_author_info(save_paths: list[Path]):
    """
    著者情報を抽出する関数
    """
    prompt = """
画像ファイルはある本の奥付けです。ここからタイトルと著者を読み取ってください  

"""
    return gemini_api_call(save_paths, prompt, AuthorInfo)

def extract_toc_info(save_paths: list[Path]):
    """
    目次情報を抽出する関数
    """
    prompt = """
画像ファイルはある本の目次ページです。ここから目次を読み取ってください。章と節の階層構造に注意してください。
"""
    return gemini_api_call(save_paths, prompt, list[Section])


def extract_page_img_to_tmp_file(input_pdf_path: Path, page_start: int, page_end: int) -> list[Path]:
    """
    ページ範囲を指定して画像を抽出する関数
    """
    images = pdf2image.convert_from_path(input_pdf_path, first_page=page_start, last_page=page_end)
    
    tmp_dir = Path("tmp")
    tmp_dir.mkdir(exist_ok=True)

    save_paths = []
    for i, image in enumerate(images):
        save_path = tmp_dir / f"page_{i+1}.png"
        image.save(save_path)
        save_paths.append(save_path)
    return save_paths


def section_to_dict(section):
    """Sectionオブジェクトを辞書に変換する関数"""
    result = {
        "title": section.title,
        "page": section.page
    }
    
    if hasattr(section, "sub_sections") and section.sub_sections:
        result["sub_sections"] = [section_to_dict(sub) for sub in section.sub_sections]
    else:
        pass
        
    if hasattr(section, "sub_sub_sections") and section.sub_sub_sections:
        result["sub_sub_sections"] = [{"title": sub.title, "page": sub.page} for sub in section.sub_sub_sections]
    else:
        pass
        
    return result


if __name__ == "__main__":
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='PDFから著者情報と目次情報を抽出してYAMLファイルに保存するプログラム')
    parser.add_argument('--input', '-i', type=str, help='入力PDFファイルのパス')
    parser.add_argument('--output', '-o', type=str, default="info.yaml", help='出力YAMLファイルのパス（デフォルトはinfo.yaml）')
    parser.add_argument('--toc-page-start', type=int, default=4, help='目次の開始ページ')
    parser.add_argument('--toc-page-end', type=int, default=7, help='目次の終了ページ')
    parser.add_argument('--author-page', type=int, default=257, help='著者情報のページ')
    parser.add_argument('--toc-page-diff', type=int, default=2, help='目次のページ番号とPDFのページ番号の差')
    
    args = parser.parse_args()

    # 引数から値を取得
    input_pdf = Path(args.input)
    
    output_yaml = Path(args.output)

    toc_page_start = args.toc_page_start
    toc_page_end = args.toc_page_end
    author_page = args.author_page
    toc_page_diff = args.toc_page_diff

    # PDFから情報を抽出
    print(f"PDFから情報を抽出中: {input_pdf}")
    
    # 著者情報を抽出
    save_paths = extract_page_img_to_tmp_file(input_pdf, author_page, author_page)
    author_response = extract_author_info(save_paths)

    print(f"著者名: {author_response.author}")
    print(f"タイトル: {author_response.title}")

    author_info = {
        "/Author": author_response.author,
        "/Title": author_response.title
    }

    # 目次情報を抽出
    save_paths = extract_page_img_to_tmp_file(input_pdf, toc_page_start, toc_page_end)
    toc_response = extract_toc_info(save_paths)

    # 目次情報を辞書のリストに変換
    toc_dict_list = [section_to_dict(section) for section in toc_response]

    # 全ての情報をまとめる
    data = {
        "input_pdf": str(input_pdf),
        "author_info": author_info,
        "toc_info": toc_dict_list,
        "toc_page_diff": toc_page_diff
    }

    # YAMLファイルに保存
    try:
        with open(output_yaml, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"情報をYAMLファイルに保存しました: {output_yaml}")
        print(f"YAMLファイルを編集後、以下のコマンドでPDFに適用できます:")
        print(f"python apply.py --input {output_yaml}")
    except Exception as e:
        print(f"YAMLファイルの保存中にエラーが発生しました: {e}")
        exit(1)