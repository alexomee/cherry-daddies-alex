// CoreMIDI probe: send messages to a port and print everything it sends back (GM-800 SysEx RQ1/DT1, see wiki/pipelines/gm-800.md).
// build: swiftc -O -o /tmp/midiq tools/midiq.swift
// usage: midiq <port> <wait_ms> <hex msg> [| <hex msg> ...]
import CoreMIDI; import Foundation
let a = CommandLine.arguments
func name(_ e: MIDIEndpointRef) -> String { var s: Unmanaged<CFString>?; MIDIObjectGetStringProperty(e, kMIDIPropertyDisplayName, &s); return (s?.takeRetainedValue() as String?) ?? "" }
var dest: MIDIEndpointRef = 0, src: MIDIEndpointRef = 0
for i in 0..<MIDIGetNumberOfDestinations() { let d = MIDIGetDestination(i); if name(d) == a[1] { dest = d } }
for i in 0..<MIDIGetNumberOfSources() { let d = MIDIGetSource(i); if name(d) == a[1] { src = d } }
guard dest != 0, src != 0 else { print("port not found"); exit(1) }
let wait = UInt32(a[2])! * 1000
var client = MIDIClientRef(); MIDIClientCreate("cd-midiq" as CFString, nil, nil, &client)
var inPort = MIDIPortRef()
MIDIInputPortCreateWithBlock(client, "in" as CFString, &inPort) { list, _ in
  var p = list.pointee.packet
  for _ in 0..<list.pointee.numPackets {
    let bytes = withUnsafeBytes(of: p.data) { Array($0.prefix(Int(p.length))) }
    print("RX", bytes.map { String(format: "%02X", $0) }.joined(separator: " "))
    p = MIDIPacketNext(&p).pointee
  }
}
MIDIPortConnectSource(inPort, src, nil)
var outPort = MIDIPortRef(); MIDIOutputPortCreate(client, "out" as CFString, &outPort)
let msgs = a.dropFirst(3).joined(separator: " ").components(separatedBy: "|")
for m in msgs {
  let bytes = m.split(separator: " ").map { UInt8($0, radix: 16)! }
  if bytes.isEmpty { continue }
  print("TX", bytes.map { String(format: "%02X", $0) }.joined(separator: " "))
  var buf = [UInt8](repeating: 0, count: 1024)
  buf.withUnsafeMutableBytes { raw in
    let pl = raw.baseAddress!.assumingMemoryBound(to: MIDIPacketList.self)
    let pk = MIDIPacketListInit(pl)
    _ = MIDIPacketListAdd(pl, 1024, pk, 0, bytes.count, bytes)
    MIDISend(outPort, dest, pl)
  }
  usleep(wait)
}
