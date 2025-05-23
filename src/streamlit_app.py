import streamlit as st
import utils.myFunc as mf


def main():
    st.title("📊 AI Model Evaluation Summary")
    analyzer = mf.ExcelAnalyzer()
 # ------------------------------------------------SIDEBAR-------------------------------------------
    st.sidebar.image("src/assets/ojk-logo-jpg.jpg")
    with st.sidebar :
        st.subheader('Settings :')
        with st.expander("General Settings :"):
            uploaded_files = st.file_uploader(
                "Unggah berkas XLSX",
                type=['xlsx'], accept_multiple_files=True)
            st.caption("Upload satu atau beberapa file Excel (.xlsx)")
            # st.markdown("---")

# ---------------------------------------------------------------------------------------------------
            if not uploaded_files:
                st.info("Silakan upload minimal satu file Excel (.xlsx).")
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
            # st.caption(f"Kolom Numerik: {' ;'.join(num_cols) if num_cols else 'Tidak ada'}")
            # st.caption(f"Kolom Kategorikal: {' ;'.join(cat_cols) if cat_cols else 'Tidak ada'}")

            if len(cat_cols) == 0:
                st.warning("Data gabungan tidak memiliki kolom kategorikal untuk analisis.")
                return

            if analyzer.verif_col not in analyzer.df.columns:
                st.warning(f"Kolom '{analyzer.verif_col}' tidak ditemukan di data gabungan.")
                return

            verif_options = analyzer.df[analyzer.verif_col].dropna().unique().tolist()
            key_options = analyzer.df[analyzer.key_col].dropna().unique().tolist()
            type_options = analyzer.df[analyzer.type_col].dropna().unique().tolist()

    tab1, tab2, tab3 = st.tabs(["📈 AI Model Eval", "📊 Analytics", "📚 Doc"])

    with tab1:
        st.header("Summary :")
        df_counts, df_metrics, df_counts_total, df_metrics_total = analyzer.calculate_confusion_stats()
        if df_counts is None or df_metrics is None:
            st.warning("Data tidak mencukupi untuk menghitung statistik (pastikan kolom berisi 'True Positive', 'True Negative', 'False Positive', 'False Negative').")
        else:
            with st.expander ("Coef Matrix:"):
                # st.subheader("Coef Matrix Per Key")
                st.dataframe(df_counts.style.format({"Count": "{:,.0f}"}))

                st.dataframe(df_counts_total.style.format({"Count": "{:,.0f}"}))
            with st.expander ("Metrics:"):
                # st.subheader("Metrics Evaluasi Per Key")
                def fmt(val):
                    return f"{val:.2f}" if val is not None else "-"
                st.dataframe(df_metrics.style.format({"Value": fmt}))

                def fmt(val):
                    return f"{val:.2f}" if val is not None else "-"
                st.dataframe(df_metrics_total.style.format({"Value": fmt}))

    with tab2:
        st.header("Bar Chart")
        with st.sidebar :
            with st.expander("Analytics Settings:"):
                # Tambahkan opsi 'All' di awal
                key_options_with_all = ['All'] + key_options
                type_options_with_all = ['All'] + type_options

                # Multiselect dengan default 'All'
                selected_key_raw = st.multiselect(
                    "Pilih Key:",
                    options=key_options_with_all,
                    default=['All']
                )

                selected_type_raw = st.multiselect(
                    "Pilih Type:",
                    options=type_options_with_all,
                    default=['All']
                )

                analyzer.category_col = st.selectbox("Pilih Kolom Kategori Y-Bar", cat_cols)

                # Logika: jika 'All' dipilih, maka ambil semua opsi asli
                analyzer.selected_key = key_options if 'All' in selected_key_raw else selected_key_raw
                analyzer.selected_type = type_options if 'All' in selected_type_raw else selected_type_raw

                analyzer.selected_verif = st.multiselect(
                    f"Pilih X-Bar '{analyzer.verif_col}'",
                    options=verif_options,
                    default=verif_options[:1]
                )

                analyzer.top_n = st.slider("Tentukan Top N: ", min_value=1, max_value=100, value=10)

                grouped, grouped_detail, grouped_with_criteria = analyzer.filter_and_group()
                
        if grouped.empty:
            st.info("Data tidak ditemukan untuk filter yang dipilih.")
        else:
            analyzer.plot_bar(grouped)
            with st.expander(f"### 📋 Tabel Detail {analyzer.category_col}:"):
                st.dataframe(grouped_detail)

            with st.expander(f"### 📋 Tabel Detail {analyzer.category_col} and Criteria:"):
                st.dataframe(grouped_with_criteria)

    with tab3:
        st.subheader("📘 Documentation")
        st.markdown("""
        ### 🚀 Getting Started

        Welcome to the AI Evaluation App! Here's how to use it:

        1. **Upload** an Excel (.xlsx) file using the sidebar.
        2. **Select** the sheet you want to work with.
        3. **Choose** the category column (e.g., verification result).
        4. Head over to the **Statistics** tab to see counts and evaluation metrics (Accuracy, F1 Score, etc.).
        5. Use the **Data Analysis** tab to explore visualizations and filter data by multiple verification types.
        6. This **Documentation** tab is here to guide you whenever you need help.

        ---

        ### 🧠 App Architecture

        - **Backend**: Data processing with `Pandas`.
        - **Visualization**: Powered by `Matplotlib` and `Seaborn`.
        - **User Interface**: Built with `Streamlit` and organized via tab navigation.

        ---

        ### 🙌 Credits & Acknowledgements

        - Created by **Naufal Nashif**
        - Built with: `Pandas`, `Streamlit`, `Matplotlib`, `Seaborn`
        - Special thanks to the open-source community and official documentation for continuous inspiration ✨

        ---

        ### 🔗 Source Code & Docs

        Full source code and technical documentation available on GitHub:

        ```
        https://github.com/naufalnashif/rfojk-sreamlit-ai-eval
        ```

        Feel free to ⭐ the repo, fork it, or contribute!

        ---
        """)


if __name__ == "__main__":
    main()
