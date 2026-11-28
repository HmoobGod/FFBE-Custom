package com.exvius.local;
import java.io.*;import java.nio.file.*;import java.security.*;import java.util.*;import java.util.concurrent.Executor;
import java.nio.charset.StandardCharsets;
/** Inactive review adapter: disposable profile only. Work runs on supplied fixture worker. */
final class Session117 implements Consent115.Completion,Supervisor91.Endpoint {
 interface Transport {String commit(String root,String pid,String token,String binding,byte[] proposal,Witness witness)throws Exception;}
 public static final class Witness {
  private final Supervisor91 owner;private final Thread thread;private volatile boolean active=true;
  Witness(Supervisor91 o){owner=o;thread=Thread.currentThread();}
  public boolean witness(){if(!active||Thread.currentThread()!=thread)return false;try{owner.requireAttempted117();return true;}catch(IOException e){return false;}}
  void end(){active=false;}
 }
 private final Path root;private final String pid,binding,expected;private final Transport transport;private final Executor worker;private Supervisor91 owner;private byte[] reviewed;private boolean attempted;volatile String outcome="WAITING";
 private static final String[] TARGETS={"state/campaign.json","state/slots/index.json","prefs/gamedata.xml","prefs/Cocos2dxPrefsFile.xml","prefs/auth.xml","files/LKCBK.dat","data/registry.json"};
 static String sha(byte[] b)throws Exception{StringBuilder s=new StringBuilder();for(byte x:MessageDigest.getInstance("SHA-256").digest(b))s.append(String.format(Locale.ROOT,"%02x",x&255));return s.toString();}
 Session117(Path root,String pid,String binding,String expected,Transport transport,Executor worker)throws Exception{if(!root.isAbsolute()||!root.toRealPath().equals(root)||!root.getFileName().toString().startsWith("ffbe117-fixture-")||!binding.matches("[0-9a-f]{64}")||!expected.matches("[0-9a-f]{64}"))throw new IOException("Fixture identity");this.root=root;this.pid=pid;this.binding=binding;this.expected=expected;this.transport=transport;this.worker=worker;}
 public synchronized void complete(byte[] bytes,String h){if(attempted)return;attempted=true;if(!binding.equals(h)){outcome="BLOCKED";return;}byte[] copy=bytes.clone();outcome="QUEUED";try{worker.execute(()->run(copy));}catch(RuntimeException e){outcome="BLOCKED";}}
 public synchronized void denied(){if(!attempted){attempted=true;outcome="CANCELLED";}}
 private void run(byte[] copy){try{if(!expected.equals(sha(copy)))throw new IOException("Wrong proposal");reviewed=copy;owner=new Supervisor91(root,this,true);owner.prepare(sha(read(TARGETS[0])),sha(read(TARGETS[1])));owner.confirm(owner.decideFixture(expected));owner.close();outcome="COMMITTED";}catch(Exception|LinkageError e){outcome="BLOCKED";}finally{reviewed=null;}}
 private byte[] read(String n)throws Exception {Path p=root.resolve(n);if(!Files.isRegularFile(p,LinkOption.NOFOLLOW_LINKS)||Files.size(p)>8*1024*1024)throw new IOException("Invalid fixture member");return Files.readAllBytes(p);}
 public String prepare(String a,String b){return expected;}
 public String confirm(String p){Witness w=new Witness(owner);try{if(!expected.equals(p)||reviewed==null||!w.witness())throw new IOException("Review unavailable");byte[][] old=new byte[7][];for(int i=0;i<7;i++){if(i>=3&&i<=5){if(Files.exists(root.resolve(TARGETS[i]),LinkOption.NOFOLLOW_LINKS))throw new IOException("Unexpected fixture member");}else old[i]=read(TARGETS[i]);}
 String b=sha(("FFBE-STARTUP-FIXTURE-114\n"+sha(old[0])+"\n"+sha(old[1])+"\n"+sha(old[6])+"\n"+sha(old[2])+"\n"+sha(reviewed)).getBytes(StandardCharsets.UTF_8));if(!binding.equals(b))throw new IOException("Stale profile");
 String token=UUID.randomUUID().toString().replace("-","");if(!(token+"\tCONFIRMED_FIXTURE_ONLY").equals(transport.commit(root.toString(),pid,token,binding,reviewed.clone(),w))||!w.witness())throw new IOException("Unverified response");
 for(int i=0;i<7;i++){if(old[i]==null){if(Files.exists(root.resolve(TARGETS[i]),LinkOption.NOFOLLOW_LINKS)||Files.exists(root.resolve("profile-backup/"+i+".bin"),LinkOption.NOFOLLOW_LINKS))throw new IOException("Unexpected member");}else if(!Arrays.equals(read(TARGETS[i]),i==0?reviewed:old[i])||!Arrays.equals(read("profile-backup/"+i+".bin"),old[i]))throw new IOException("Readback mismatch");}
 // Independently derive the exact canonical profile manifest and schema3 record.
 TreeMap<String,byte[]> sorted=new TreeMap<>();for(int i=0;i<7;i++)sorted.put(TARGETS[i],old[i]);StringBuilder m=new StringBuilder("{");boolean first=true;for(Map.Entry<String,byte[]> e:sorted.entrySet()){if(!first)m.append(',');first=false;m.append('"').append(e.getKey()).append("\":");byte[] v=e.getValue();if(v==null)m.append("null");else m.append("{\"bytes\":").append(v.length).append(",\"sha256\":\"").append(sha(v)).append("\"}");}byte[] manifest=m.append('}').toString().getBytes(StandardCharsets.US_ASCII);
 byte[] record=("{\"catalogue\":\""+sha(old[1])+"\",\"original\":\""+sha(old[0])+"\",\"profile\":\""+sha(manifest)+"\",\"proposed\":\""+sha(reviewed)+"\",\"schema\":3}").getBytes(StandardCharsets.US_ASCII);
 if(!Arrays.equals(manifest,read("profile-backup/manifest.json"))||!Arrays.equals(manifest,read("profile-backup/complete.json"))||!Arrays.equals(record,read("transaction-backup/intent.json"))||!Arrays.equals(record,read("transaction-backup/committed.json"))||!Arrays.equals(old[0],read("transaction-backup/campaign.before-first-write.json"))||!w.witness())throw new IOException("Record mismatch");
 return "CONFIRMED_FIXTURE_ONLY";
 }catch(Exception e){throw new IllegalStateException(e);}finally{w.end();}}
 public void drain(){if(!"CONFIRMED".equals(owner.state()))throw new IllegalStateException("Uncertain ownership retained");}
}
