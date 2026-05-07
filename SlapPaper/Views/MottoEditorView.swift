import SwiftUI

struct MottoEditorView: View {
    @ObservedObject var store: MottoStore
    var onRefresh: () -> Void
    var onQuit: () -> Void
    var onAutostartChange: (Bool) -> Void

    @AppStorage("autostart") private var loginAutostart = false

    @State private var newMotto = ""
    @State private var editingIndex: Int?
    @State private var editingText = ""
    @State private var statusMessage = ""
    @State private var statusIsError = false
    @State private var deleteTarget: Int?

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("文案库")
                .font(.headline)

            HStack {
                TextField("新增一句文案...", text: $newMotto)
                    .textFieldStyle(.roundedBorder)
                Button {
                    addMotto()
                } label: {
                    Label("添加", systemImage: "plus.circle.fill")
                }
                .keyboardShortcut(.defaultAction)
            }

            Text(statusMessage)
                .font(.caption)
                .foregroundColor(statusIsError ? .red : .secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
                .frame(minHeight: 16)

            List {
                if store.mottos.isEmpty && store.loadErrorMessage == nil {
                    VStack(spacing: 8) {
                        Image(systemName: "quote.bubble")
                            .font(.system(size: 40))
                            .foregroundColor(.secondary)
                        Text("还没有文案，先在上方输入一句。")
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 32)
                    .listRowBackground(Color.clear)
                } else {
                    ForEach(store.indexedMottos) { item in
                        mottoRow(index: item.index, text: item.text)
                    }
                }
            }
            .listStyle(.inset(alternatesRowBackgrounds: false))

            Toggle("登录时自动启动", isOn: $loginAutostart)
                .font(.subheadline)
                .onChange(of: loginAutostart) { newValue in
                    onAutostartChange(newValue)
                    setStatus(newValue ? "开机自启已开启。" : "开机自启已关闭。")
                }

            HStack {
                Button {
                    onRefresh()
                } label: {
                    Label("刷新壁纸", systemImage: "arrow.clockwise")
                }
                Spacer()
                Button("退出", role: .destructive) {
                    onQuit()
                }
            }
        }
        .padding(16)
        .frame(minWidth: 460, minHeight: 460)
        .background(.ultraThinMaterial)
        .onAppear {
            store.reloadFromDisk()
            if let err = store.loadErrorMessage {
                setStatus(err, error: true)
            }
        }
        .confirmationDialog(
            "删除这条文案？",
            isPresented: Binding(
                get: { deleteTarget != nil },
                set: { if !$0 { deleteTarget = nil } }
            ),
            titleVisibility: .visible
        ) {
            Button("删除", role: .destructive) {
                if let i = deleteTarget {
                    deleteMotto(at: i)
                }
                deleteTarget = nil
            }
            Button("取消", role: .cancel) {
                deleteTarget = nil
            }
        } message: {
            Text("删除后会立即从文案库中移除。")
        }
    }

    @ViewBuilder
    private func mottoRow(index: Int, text: String) -> some View {
        if editingIndex == index {
            VStack(alignment: .leading, spacing: 8) {
                TextField("编辑文案", text: $editingText, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(2...4)
                HStack {
                    Button("保存") {
                        saveEdit(at: index)
                    }
                    .keyboardShortcut(.defaultAction)
                    Button("取消") {
                        cancelEdit()
                    }
                }
            }
            .padding(.vertical, 4)
        } else {
            HStack(alignment: .top) {
                Text(text)
                    .font(.body)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .multilineTextAlignment(.leading)
                Button {
                    beginEdit(index: index, text: text)
                } label: {
                    Image(systemName: "pencil")
                }
                .buttonStyle(.borderless)
                .help("编辑")
                Button {
                    deleteTarget = index
                } label: {
                    Image(systemName: "trash")
                }
                .buttonStyle(.borderless)
                .help("删除")
            }
            .padding(.vertical, 4)
        }
    }

    private func setStatus(_ message: String, error: Bool = false) {
        statusMessage = message
        statusIsError = error
    }

    private func addMotto() {
        let trimmed = newMotto.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            setStatus("文案不能为空。", error: true)
            return
        }
        let duplicate = store.mottos.contains(trimmed)
        do {
            try store.addMotto(trimmed)
            newMotto = ""
            setStatus(duplicate ? "已添加，但这条文案和现有内容重复。" : "文案已添加。")
        } catch {
            setStatus(error.localizedDescription, error: true)
        }
    }

    private func beginEdit(index: Int, text: String) {
        editingIndex = index
        editingText = text
        setStatus("")
    }

    private func cancelEdit() {
        editingIndex = nil
        editingText = ""
        setStatus("")
    }

    private func saveEdit(at index: Int) {
        do {
            try store.updateMotto(at: index, text: editingText)
            cancelEdit()
            setStatus("文案已保存。")
        } catch {
            setStatus(error.localizedDescription, error: true)
        }
    }

    private func deleteMotto(at index: Int) {
        do {
            try store.deleteMotto(at: index)
            cancelEdit()
            setStatus("文案已删除。")
        } catch {
            setStatus(error.localizedDescription, error: true)
        }
    }
}
