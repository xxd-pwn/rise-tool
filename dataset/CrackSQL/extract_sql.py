import json
import os


def extract_sql(input_file, sql_type, output_dir):
    """
    Extract SQL statements from JSON file and save them as numbered SQL files.
    
    Args:
        input_file: Path to the input JSON file
        sql_type: Type of SQL to extract (e.g., 'pg', 'cracksql', 'sqlglot', 'jooq', 'llm', 'sqlines')
        output_dir: Directory to save the extracted SQL files
    """
    # Read the JSON file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON from '{input_file}'.")
        return
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Extract and save SQL statements
    saved_count = 0
    for idx, item in enumerate(data, start=1):
        if sql_type in item:
            sql_content = item[sql_type]
            output_file = os.path.join(output_dir, f"{idx}.sql")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(sql_content)
            
            saved_count += 1
        else:
            print(f"Warning: Item {idx} does not have '{sql_type}' field, skipping...")
    
    print(f"\nSuccessfully extracted {saved_count} SQL statements to {output_dir}")


def main():
    extract_sql('D:\\work\\project\\rise-tool\\dataset\\CrackSQL\\exp_res_cracksql\\mysql_to_oracle_data.json', 'mysql', 'D:\\work\\project\\rise-tool\\dataset\\CrackSQL\\MySQL-Oracle')


if __name__ == '__main__':
    main()
