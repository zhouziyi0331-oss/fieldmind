//
//  fieldmindApp.swift
//  fieldmind
//
//  Created by alwan on 2026/9/11.
//

import SwiftUI

@main
struct fieldmindApp: App {
    var body: some Scene {
        DocumentGroup(newDocument: fieldmindDocument()) { file in
            ContentView(document: file.$document)
        }
    }
}
