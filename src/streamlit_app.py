import os
os.environ['HOME'] = '/root'
os.environ['STREAMLIT_CONFIG_DIR'] = '/root/.streamlit'

import streamlit as st
import utils.myFunc as mf


def main():
    st.title("📊 AI Model Evaluation Summary")

    analyzer = mf.ExcelAnalyzer()

    st.sidebar.image("src/assets/ojk-logo-jpg.jpg")

    st.sidebar.header("📥 Upload & Pilih Parameter")

    uploaded_files = st.sidebar.file_uploader(
        "Upload satu atau beberapa file Excel (.xlsx)",
        type=['xlsx'], accept_multiple_files=True)


    if not uploaded_files:
        st.info("Silakan upload minimal satu file Excel (.xlsx) di sidebar.")
        return

    sheets = analyzer.get_all_sheet_names(uploaded_files)
    if not sheets:
        st.warning("Tidak ada sheet ditemukan di file yang diupload.")
        return
    default_sheet = "Sheet1"
    sheet_choice = default_sheet if default_sheet in sheets else sheets[0]


    combined_df = analyzer.load_and_concat_sheets(uploaded_files, sheet_choice)
    if combined_df is None or combined_df.empty:
        st.warning("Data gabungan kosong atau gagal dibaca.")
        return

    analyzer.df = combined_df

    num_cols, cat_cols = analyzer.get_columns()
    st.sidebar.markdown(f"**Kolom Numerik:** {' ; '.join(num_cols) if num_cols else 'Tidak ada'}")
    st.sidebar.markdown(f"**Kolom Kategorikal:** {' ; '.join(cat_cols) if cat_cols else 'Tidak ada'}")

    if len(cat_cols) == 0:
        st.warning("Data gabungan tidak memiliki kolom kategorikal untuk analisis.")
        return

    if analyzer.verif_col not in analyzer.df.columns:
        st.warning(f"Kolom '{analyzer.verif_col}' tidak ditemukan di data gabungan.")
        return

    verif_options = analyzer.df[analyzer.verif_col].dropna().unique().tolist()

    tab1, tab2, tab3 = st.tabs(["📈 Statistik Verifikasi", "📊 Analisis Data", "📚 Dokumentasi"])

    with tab1:
        st.header("Summary :")
        df_counts, df_metrics = analyzer.calculate_confusion_stats()
        if df_counts is None or df_metrics is None:
            st.warning("Data tidak mencukupi untuk menghitung statistik (pastikan kolom berisi 'True Positive', 'True Negative', 'False Positive', 'False Negative').")
        else:
            st.subheader("Coef Matrix")
            st.dataframe(df_counts.style.format({"Count": "{:,.0f}"}))

            st.subheader("Metrics Evaluasi")
            def fmt(val):
                return f"{val:.4f}" if val is not None else "-"
            st.dataframe(df_metrics.style.format({"Value": fmt}))

    with tab2:
        st.header("Analisis Bar Chart dengan Filter Multi Verifikasi")

        analyzer.category_col = st.selectbox("Pilih Kolom Kategori untuk Analisis", cat_cols)

        analyzer.selected_verif = st.multiselect(
            f"Pilih satu atau beberapa kondisi '{analyzer.verif_col}'",
            options=verif_options,
            default=verif_options[:1]
        )

        analyzer.top_n = st.slider("Pilih Top N kategori untuk ditampilkan", min_value=1, max_value=100, value=10)

        grouped = analyzer.filter_and_group()
        if grouped.empty:
            st.info("Data tidak ditemukan untuk filter yang dipilih.")
        else:
            analyzer.plot_bar(grouped)
            st.write("### 📋 Tabel Detail")
            st.dataframe(grouped)

    with tab3:
        st.header("Documentation")
        st.markdown("""
        ## How to Use the App

        1. Upload an Excel (.xlsx) file using the sidebar.
        2. Select the sheet you want to analyze.
        3. Choose the category column for analysis.
        4. **Statistics Tab**: Displays counts and evaluation metrics based on verification categories.
        5. **Data Analysis Tab**: Shows visualizations and tables with multi-verification filters.
        6. **Documentation Tab**: Contains usage info and app credits.

        ---

        ## App Architecture
        - **Backend**: Data manipulation with Pandas.
        - **Visualization**: Matplotlib and Seaborn.
        - **User Interface**: Streamlit with tab navigation.

        ---

        ## Credits
        - Created by Naufal Nashif Imanuddin  
        - Libraries used: Pandas, Streamlit, Matplotlib, Seaborn  
        - Special thanks to the open-source community and official documentation.

        ---
        """)


if __name__ == "__main__":
    main()
