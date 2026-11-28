import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1]);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==sys.argv[3]
s=raw.decode();start=s.index(' static final class Review {');end=s.index(' private static Object parse(')
s=s[:start]+''' /** Review only the independently identified exact startup additions on the synthetic fixture. */
 @SuppressWarnings("unchecked") static void verify(byte[] before, byte[] after)throws Exception {
  Map<String,Object> expected=(Map<String,Object>)parse(before);
  Map<String,Object> result=(Map<String,Object>)parse(after);
  if(expected.containsKey("exvius_resource_recovery"))throw bad();
  Map<String,Object> progress=(Map<String,Object>)expected.get("progress");
  Object raw=progress.get("switches");if(!(raw instanceof Map))throw bad();
  Map<String,Object> switches=(Map<String,Object>)raw;
  if(switches.containsKey("101"))throw bad();
  switches.put("101",Collections.emptyList());
  Map<String,Object> recovery=new LinkedHashMap<>();
  recovery.put("complete",true);recovery.put("legacy_signature_detected",false);recovery.put("restored_scene_switches",Collections.emptyList());
  expected.put("exvius_resource_recovery",recovery);
  if(!expected.equals(result))throw bad();
 }
'''+s[end:]
s=s.replace('final class SemanticReview94','final class StartupReview114').replace('Receipt93.MAX','8*1024*1024')
pathlib.Path(sys.argv[2]).write_text(s)
