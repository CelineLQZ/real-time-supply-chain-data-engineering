#!/usr/bin/env python3
"""
数据探索脚本: DataCoSupplyChainDataset.csv
用于查看数据的变量、格式、范围和质量
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_data(file_path):
    """加载 CSV 文件"""
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f'✅ 数据加载成功')
        print(f'📊 数据集大小: {df.shape[0]:,} 行 × {df.shape[1]} 列\n')
        return df
    except FileNotFoundError:
        print(f'❌ 文件未找到: {file_path}')
        return None


def show_basic_info(df):
    """显示数据基本信息"""
    print('=' * 80)
    print('📋 数据基本信息')
    print('=' * 80)
    print('\n前 5 行数据:')
    print(df.head())
    print(f'\n数据集大小: {df.shape[0]:,} 行 × {df.shape[1]} 列')


def show_data_types(df):
    """显示数据类型"""
    print('\n' + '=' * 80)
    print('🔍 数据类型分析')
    print('=' * 80)
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    print(f'\n📊 数据类型统计:')
    print(f'  数值型列: {len(numeric_cols)}')
    print(f'  对象型列: {len(categorical_cols)}')
    
    print('\n📋 每列的数据类型:')
    dtype_info = pd.DataFrame({
        '列名': df.columns,
        '数据类型': df.dtypes.values,
        '非空值': df.count().values,
        '总值': len(df)
    })
    print(dtype_info.to_string(index=False))


def show_numeric_analysis(df):
    """显示数值变量分析"""
    print('\n' + '=' * 80)
    print('📈 数值变量分析')
    print('=' * 80)
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    if len(numeric_cols) == 0:
        print('⚠️ 没有数值型变量')
        return
    
    print('\n基础统计信息:')
    print(df[numeric_cols].describe())
    
    print('\n\n详细范围分析:')
    for col in numeric_cols:
        print(f'\n🔹 {col}:')
        print(f'    最小值:  {df[col].min():>15,.2f}')
        print(f'    最大值:  {df[col].max():>15,.2f}')
        print(f'    范围:    {df[col].max() - df[col].min():>15,.2f}')
        print(f'    均值:    {df[col].mean():>15,.2f}')
        print(f'    中位数:  {df[col].median():>15,.2f}')
        print(f'    标准差:  {df[col].std():>15,.2f}')
        print(f'    25%分位: {df[col].quantile(0.25):>15,.2f}')
        print(f'    75%分位: {df[col].quantile(0.75):>15,.2f}')
        print(f'    IQR:    {df[col].quantile(0.75) - df[col].quantile(0.25):>15,.2f}')


def show_categorical_analysis(df):
    """显示分类变量分析"""
    print('\n' + '=' * 80)
    print('🏷️ 分类变量分析')
    print('=' * 80)
    
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    if len(categorical_cols) == 0:
        print('⚠️ 没有分类型变量')
        return
    
    for col in categorical_cols:
        unique_count = df[col].nunique()
        print(f'\n🔹 {col}:')
        print(f'    唯一值个数: {unique_count}')
        print(f'    最常见的 10 个值:')
        
        value_counts = df[col].value_counts().head(10)
        for idx, (value, count) in enumerate(value_counts.items(), 1):
            percentage = (count / len(df)) * 100
            print(f'      {idx:2d}. {str(value)[:50]:50s} - {count:>8,} ({percentage:>5.2f}%)')


def show_missing_values(df):
    """显示缺失值分析"""
    print('\n' + '=' * 80)
    print('🔴 缺失值分析')
    print('=' * 80)
    
    missing_info = pd.DataFrame({
        '列名': df.columns,
        '缺失值数': df.isnull().sum().values,
        '缺失值比例': (df.isnull().sum().values / len(df) * 100).round(2)
    })
    
    missing_info_filtered = missing_info[missing_info['缺失值数'] > 0].sort_values('缺失值数', ascending=False)
    
    if len(missing_info_filtered) > 0:
        print('\n有缺失值的列:')
        print(missing_info_filtered.to_string(index=False))
    else:
        print('\n✅ 没有缺失值')
    
    total_missing = df.isnull().sum().sum()
    total_cells = len(df) * len(df.columns)
    print(f'\n总缺失值: {total_missing:,} / {total_cells:,} ({(total_missing/total_cells*100):.4f}%)')


def show_data_quality_summary(df):
    """显示数据质量总结"""
    print('\n' + '=' * 80)
    print('📊 数据质量总结')
    print('=' * 80)
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    total_missing = df.isnull().sum().sum()
    total_cells = len(df) * len(df.columns)
    
    print(f'\n总记录数:      {len(df):>15,}')
    print(f'总列数:        {len(df.columns):>15,}')
    print(f'\n数值型列:      {len(numeric_cols):>15}')
    print(f'分类型列:      {len(categorical_cols):>15}')
    print(f'\n缺失值总数:    {total_missing:>15,}')
    print(f'缺失值比例:    {(total_missing/total_cells*100):>15.4f}%')
    print(f'数据完整性:    {((1-total_missing/total_cells)*100):>15.2f}%')


def export_data_dictionary(df, output_file='data_dictionary.csv'):
    """导出数据字典"""
    print('\n' + '=' * 80)
    print('📖 导出数据字典')
    print('=' * 80)
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    data_dict = pd.DataFrame({
        '列名': df.columns,
        '数据类型': df.dtypes.values,
        '非空值': df.count().values,
        '缺失值': df.isnull().sum().values,
        '唯一值': [df[col].nunique() for col in df.columns],
        '最小值': [f'{df[col].min():.2f}' if col in numeric_cols else '-' for col in df.columns],
        '最大值': [f'{df[col].max():.2f}' if col in numeric_cols else '-' for col in df.columns]
    })
    
    data_dict.to_csv(output_file, index=False)
    print(f'\n✅ 数据字典已保存: {output_file}')
    print(f'\n数据字典预览:')
    print(data_dict.to_string(index=False))


def main():
    """主函数"""
    # 获取数据文件路径
    current_dir = Path(__file__).parent
    file_path = current_dir / 'DataCoSupplyChainDataset.csv'
    
    # 加载数据
    df = load_data(str(file_path))
    if df is None:
        return
    
    # 显示各种分析
    show_basic_info(df)
    show_data_types(df)
    show_numeric_analysis(df)
    show_categorical_analysis(df)
    show_missing_values(df)
    show_data_quality_summary(df)
    export_data_dictionary(df)
    
    print('\n' + '=' * 80)
    print('✅ 数据探索完成！')
    print('=' * 80)


if __name__ == '__main__':
    main()
