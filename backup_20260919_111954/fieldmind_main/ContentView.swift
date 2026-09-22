//
//  ContentView.swift
//  fieldmind
//
//  Created by alwan on 2026/9/11.
//  Updated: 2026/9/19 - 集成第二大脑蒸馏系统
//

import SwiftUI

struct ContentView: View {
    @Binding var document: fieldmindDocument

    var body: some View {
        MainNavigationView()
    }
}

#Preview {
    ContentView(document: .constant(fieldmindDocument()))
}
