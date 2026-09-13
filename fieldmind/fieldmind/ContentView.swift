//
//  ContentView.swift
//  fieldmind
//
//  Created by alwan on 2026/9/11.
//

import SwiftUI

struct ContentView: View {
    @Binding var document: fieldmindDocument

    var body: some View {
        TextEditor(text: $document.text)
    }
}

#Preview {
    ContentView(document: .constant(fieldmindDocument()))
}
